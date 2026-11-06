"""Graphe de connaissances NetworkX et parcours multi-hop."""

from __future__ import annotations

import json
import math
import re
from collections import Counter, deque
from pathlib import Path
from typing import Any, Iterable

import networkx as nx

from .config import EDGES_PATH, NODES_PATH, RESULTS_DIR
from .corpus import load_edges, load_nodes, normalize


TYPE_PRIORITY = {
    "Portefeuille": 12,
    "Scénario": 11,
    "Position": 10,
    "Politique": 9,
    "Approbation": 8,
    "Contrôle": 7,
    "Facteur": 6,
    "Watchlist": 5,
    "Émetteur": 4,
    "Secteur": 3,
    "Métrique": 2,
    "Risque": 2,
    "Document": 1,
}


class KnowledgeGraph:
    def __init__(self, nodes: list[dict], edges: list[dict]):
        self.nodes = {node["id"]: node for node in nodes}
        self.edges = edges
        self.graph = nx.DiGraph()
        for node in nodes:
            self.graph.add_node(node["id"], **node)
        for edge in edges:
            if edge["head"] in self.nodes and edge["tail"] in self.nodes:
                self.graph.add_edge(
                    edge["head"],
                    edge["tail"],
                    key=edge.get("id", ""),
                    relation=edge["relation"],
                    docs=edge.get("docs", []),
                    evidence=edge.get("evidence", ""),
                    weight=edge.get("weight", 1.0),
                )
        self.undirected = self.graph.to_undirected()
        self.alias_map: dict[str, list[str]] = {}
        for node in nodes:
            for alias in {node["label"], *node.get("aliases", [])}:
                key = normalize(alias)
                if len(key) < 2:
                    continue
                self.alias_map.setdefault(key, [])
                if node["id"] not in self.alias_map[key]:
                    self.alias_map[key].append(node["id"])

    # ------------------------------------------------------------------
    # Chargement / export
    # ------------------------------------------------------------------
    @classmethod
    def from_files(cls, nodes_path: Path | None = None, edges_path: Path | None = None) -> "KnowledgeGraph":
        return cls(load_nodes(nodes_path or NODES_PATH), load_edges(edges_path or EDGES_PATH))

    def save_json(self, path: Path | None = None) -> Path:
        path = path or (RESULTS_DIR / "graph.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "stats": self.stats(),
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def save_cypher(self, path: Path | None = None) -> Path:
        path = path or (RESULTS_DIR / "graph.cypher")
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["// QuantAgent — export Neo4j", "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE;", ""]
        for node in self.nodes.values():
            props = {
                "id": node["id"],
                "label": node["label"],
                "type": node["type"],
                "description": node.get("description", ""),
            }
            props.update({k: v for k, v in node.get("properties", {}).items() if isinstance(v, (str, int, float, bool))})
            prop_text = ", ".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in props.items())
            lines.append(f"MERGE (n:Entity {{id: {json.dumps(node['id'], ensure_ascii=False)}}}) SET n += {{{prop_text}}};")
        lines.append("")
        for edge in self.edges:
            relation = re.sub(r"[^A-Z0-9_]", "_", edge["relation"].upper())
            lines.append(
                "MATCH (a:Entity {id: %s}), (b:Entity {id: %s}) "
                "MERGE (a)-[r:%s]->(b) SET r.docs = %s, r.evidence = %s;"
                % (
                    json.dumps(edge["head"], ensure_ascii=False),
                    json.dumps(edge["tail"], ensure_ascii=False),
                    relation,
                    json.dumps(edge.get("docs", []), ensure_ascii=False),
                    json.dumps(edge.get("evidence", ""), ensure_ascii=False),
                )
            )
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    # Accès de base
    # ------------------------------------------------------------------
    def node(self, node_id: str) -> dict | None:
        return self.nodes.get(node_id)

    def label(self, node_id: str) -> str:
        node = self.nodes.get(node_id)
        return node["label"] if node else node_id

    def type_of(self, node_id: str) -> str:
        node = self.nodes.get(node_id)
        return node["type"] if node else ""

    def find_entities(self, text: str, max_entities: int = 10) -> list[str]:
        normalized = normalize(text)
        candidates: list[tuple[float, str]] = []
        for alias, ids in self.alias_map.items():
            if len(alias) < 2:
                continue
            pattern = r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])"
            if re.search(pattern, normalized):
                for node_id in ids:
                    node = self.nodes.get(node_id, {})
                    score = len(alias) + 0.15 * TYPE_PRIORITY.get(node.get("type", ""), 0)
                    candidates.append((score, node_id))
        candidates.sort(key=lambda item: item[0], reverse=True)
        selected: list[str] = []
        for _, node_id in candidates:
            if node_id not in selected:
                selected.append(node_id)
            if len(selected) >= max_entities:
                break
        return selected

    def outgoing(self, node_id: str) -> list[dict]:
        rows = []
        for _, tail, data in self.graph.out_edges(node_id, data=True):
            rows.append({"head": node_id, "tail": tail, "relation": data.get("relation", ""), "docs": data.get("docs", []), "evidence": data.get("evidence", "")})
        return rows

    def incoming(self, node_id: str) -> list[dict]:
        rows = []
        for head, _, data in self.graph.in_edges(node_id, data=True):
            rows.append({"head": head, "tail": node_id, "relation": data.get("relation", ""), "docs": data.get("docs", []), "evidence": data.get("evidence", "")})
        return rows

    def neighbors(self, node_id: str, relation: str | None = None) -> list[str]:
        result = []
        for _, tail, data in self.graph.out_edges(node_id, data=True):
            if relation is None or data.get("relation") == relation:
                if tail not in result:
                    result.append(tail)
        return result

    def profile(self, node_id: str, allowed: set[str] | None = None) -> dict[str, list[str]]:
        profile: dict[str, list[str]] = {}
        for row in self.outgoing(node_id):
            if allowed and row["relation"] not in allowed:
                continue
            profile.setdefault(row["relation"], []).append(row["tail"])
        return profile

    # ------------------------------------------------------------------
    # Parcours multi-hop
    # ------------------------------------------------------------------
    def traverse(self, seeds: Iterable[str], depth: int = 2, max_paths: int = 60, max_nodes: int = 80) -> list[dict[str, Any]]:
        paths: list[dict[str, Any]] = []
        visited_global: set[str] = set()
        for seed in seeds:
            if seed not in self.nodes:
                continue
            stack: list[tuple[str, list[str], list[dict]]] = [(seed, [seed], [])]
            local_count = 0
            while stack and local_count < max_paths:
                current, node_path, edge_path = stack.pop()
                if len(node_path) > 1:
                    score = sum(1.0 / max(len(edge_path), 1) for _ in edge_path)
                    paths.append({
                        "seed": seed,
                        "nodes": node_path,
                        "chain": edge_path,
                        "depth": len(node_path) - 1,
                        "score": round(score, 4),
                    })
                    local_count += 1
                if len(node_path) - 1 >= depth:
                    continue
                for row in self.outgoing(current):
                    tail = row["tail"]
                    if tail in node_path:
                        continue
                    if len(visited_global) >= max_nodes and tail not in visited_global:
                        continue
                    visited_global.add(tail)
                    stack.append((tail, node_path + [tail], edge_path + [row]))
        paths.sort(key=lambda item: (item["depth"], item["score"]), reverse=True)
        return paths[:max_paths]

    def paths_between(self, source: str, target: str, max_length: int = 4, limit: int = 8) -> list[dict[str, Any]]:
        if source not in self.nodes or target not in self.nodes:
            return []
        try:
            raw_paths = list(nx.all_simple_paths(self.undirected, source, target, cutoff=max_length))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
        payloads = []
        for node_path in raw_paths[:limit]:
            chain = []
            for head, tail in zip(node_path, node_path[1:]):
                if self.graph.has_edge(head, tail):
                    data = self.graph.get_edge_data(head, tail)
                    chain.append({"head": head, "tail": tail, "relation": data.get("relation", ""), "docs": data.get("docs", []), "evidence": data.get("evidence", ""), "direction": "forward"})
                elif self.graph.has_edge(tail, head):
                    data = self.graph.get_edge_data(tail, head)
                    chain.append({"head": tail, "tail": head, "relation": data.get("relation", ""), "docs": data.get("docs", []), "evidence": data.get("evidence", ""), "direction": "reverse"})
                else:
                    chain.append({"head": head, "tail": tail, "relation": "LINK", "docs": [], "evidence": "", "direction": "unknown"})
            payloads.append({"source": source, "target": target, "nodes": node_path, "chain": chain, "length": len(chain)})
        return payloads

    def subgraph(self, seeds: Iterable[str], depth: int = 2, max_nodes: int = 70) -> dict[str, Any]:
        selected: list[str] = []
        queue = deque((seed, 0) for seed in seeds if seed in self.nodes)
        while queue and len(selected) < max_nodes:
            node_id, level = queue.popleft()
            if node_id in selected:
                continue
            selected.append(node_id)
            if level >= depth:
                continue
            for neighbor in list(self.graph.successors(node_id)) + list(self.graph.predecessors(node_id)):
                if neighbor not in selected:
                    queue.append((neighbor, level + 1))
        selected_set = set(selected)
        nodes = [
            {
                "id": node_id,
                "label": self.nodes[node_id]["label"],
                "type": self.nodes[node_id]["type"],
                "description": self.nodes[node_id].get("description", ""),
                "properties": self.nodes[node_id].get("properties", {}),
            }
            for node_id in selected
        ]
        edges = [
            edge for edge in self.edges
            if edge["head"] in selected_set and edge["tail"] in selected_set
        ]
        return {"nodes": nodes, "edges": edges, "seed_count": len(list(seeds))}

    def common_neighbors(self, first: str, second: str) -> list[str]:
        if first not in self.nodes or second not in self.nodes:
            return []
        return sorted(set(self.undirected.neighbors(first)) & set(self.undirected.neighbors(second)))

    # ------------------------------------------------------------------
    # Statistiques
    # ------------------------------------------------------------------
    def stats(self) -> dict[str, Any]:
        node_types = Counter(node["type"] for node in self.nodes.values())
        relations = Counter(edge["relation"] for edge in self.edges)
        degrees = dict(self.graph.degree())
        top_nodes = sorted(degrees.items(), key=lambda item: item[1], reverse=True)[:10]
        components = list(nx.connected_components(self.undirected))
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "node_types": dict(sorted(node_types.items())),
            "relations": dict(sorted(relations.items())),
            "density": round(nx.density(self.graph), 4),
            "components": len(components),
            "largest_component": max((len(c) for c in components), default=0),
            "avg_degree": round(sum(degrees.values()) / max(len(degrees), 1), 2),
            "top_nodes": [
                {"id": node_id, "label": self.label(node_id), "type": self.type_of(node_id), "degree": degree}
                for node_id, degree in top_nodes
            ],
        }

    def document_ids(self, node_ids: Iterable[str]) -> list[str]:
        docs: list[str] = []
        for node_id in node_ids:
            node = self.nodes.get(node_id, {})
            for doc in node.get("docs", []):
                if doc not in docs:
                    docs.append(doc)
        return docs
