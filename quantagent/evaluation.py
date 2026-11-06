"""Protocole d'évaluation 0-5 : baseline vectorielle vs agent hybride."""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import COMPARISON_PATH, RESULTS_DIR
from .corpus import Question, normalize

WEIGHTS = {
    "keyword_recall": 0.25,
    "numeric_accuracy": 0.25,
    "citation": 0.20,
    "graph_path": 0.15,
    "multi_hop": 0.15,
}

METRICS = ["pertinence", "exactitude", "tracabilite", "multi_hop", "score_global"]


def _numbers(text: str) -> list[float]:
    values = []
    for raw in re.findall(r"[-+]?\d+(?:[.,]\d+)?", text or ""):
        try:
            values.append(float(raw.replace(",", ".")))
        except ValueError:
            continue
    return values


def _number_present(expected: float, found: list[float]) -> bool:
    tolerance = max(0.011, abs(expected) * 0.015)
    return any(abs(value - expected) <= tolerance for value in found)


def _keyword_present(keyword: str, normalized_answer: str) -> bool:
    key = normalize(keyword)
    return bool(key) and key in normalized_answer


def score_answer(answer: dict[str, Any], question: Question, graph=None) -> dict[str, Any]:
    text = answer.get("answer", "")
    normalized_answer = normalize(text)
    found_numbers = _numbers(text)
    keywords = question.keywords or []
    keyword_hits = sum(1 for keyword in keywords if _keyword_present(keyword, normalized_answer))
    keyword_recall = keyword_hits / max(len(keywords), 1)
    numeric_hits = sum(1 for value in question.expected_numbers if _number_present(value, found_numbers))
    numeric_accuracy = numeric_hits / max(len(question.expected_numbers), 1) if question.expected_numbers else 1.0
    source_ids = {source.get("doc_id") for source in answer.get("sources", [])}
    citation_hits = sum(1 for doc_id in question.expected_docs if doc_id in source_ids)
    citation = citation_hits / max(len(question.expected_docs), 1)
    paths = answer.get("graph", {}).get("paths", [])
    graph_path = 1.0 if paths else (0.4 if answer.get("graph", {}).get("nodes") else 0.0)
    entity_set = set(answer.get("entities", []))
    multi_hits = 0
    for entity in question.expected_entities:
        label = graph.label(entity) if graph and graph.node(entity) else entity
        variants = {entity, label, label.split(" ", 1)[-1], label.replace("-", " ")}
        if entity in entity_set or any(normalize(variant) in normalized_answer for variant in variants if variant):
            multi_hits += 1
    multi_hop = multi_hits / max(len(question.expected_entities), 1)
    score = 5.0 * (
        WEIGHTS["keyword_recall"] * keyword_recall
        + WEIGHTS["numeric_accuracy"] * numeric_accuracy
        + WEIGHTS["citation"] * citation
        + WEIGHTS["graph_path"] * graph_path
        + WEIGHTS["multi_hop"] * multi_hop
    )
    return {
        "keyword_recall": round(keyword_recall, 3),
        "numeric_accuracy": round(numeric_accuracy, 3),
        "citation": round(citation, 3),
        "graph_path": round(graph_path, 3),
        "multi_hop": round(multi_hop, 3),
        "pertinence": round(5.0 * keyword_recall, 2),
        "exactitude": round(5.0 * numeric_accuracy, 2),
        "tracabilite": round(5.0 * (0.6 * citation + 0.4 * graph_path), 2),
        "multi_hop_score": round(5.0 * multi_hop, 2),
        "score_global": round(score, 2),
    }


def _aggregate(rows: list[dict]) -> dict[str, float]:
    if not rows:
        return {metric: 0.0 for metric in METRICS}
    return {
        "pertinence": round(sum(row["pertinence"] for row in rows) / len(rows), 2),
        "exactitude": round(sum(row["exactitude"] for row in rows) / len(rows), 2),
        "tracabilite": round(sum(row["tracabilite"] for row in rows) / len(rows), 2),
        "multi_hop": round(sum(row["multi_hop_score"] for row in rows) / len(rows), 2),
        "score_global": round(sum(row["score_global"] for row in rows) / len(rows), 2),
    }


def run_comparison(agent, questions: list[Question], graph=None) -> dict[str, Any]:
    rows = []
    for question in questions:
        vector_answer = agent.ask(question.question, mode="vector", evaluation_baseline=True)
        hybrid_answer = agent.ask(question.question, mode="hybrid")
        vector_scores = score_answer(vector_answer, question, graph)
        hybrid_scores = score_answer(hybrid_answer, question, graph)
        rows.append({
            "id": question.id,
            "question": question.question,
            "difficulty": question.difficulty,
            "hops": question.hops,
            "vector": vector_scores,
            "hybrid": hybrid_scores,
            "delta": round(hybrid_scores["score_global"] - vector_scores["score_global"], 2),
            "vector_sources": [source["doc_id"] for source in vector_answer.get("sources", [])],
            "hybrid_sources": [source["doc_id"] for source in hybrid_answer.get("sources", [])],
            "hybrid_hitl": hybrid_answer.get("hitl", {}).get("status"),
        })
    vector_aggregate = _aggregate([row["vector"] for row in rows])
    hybrid_aggregate = _aggregate([row["hybrid"] for row in rows])
    graph_wins = sum(1 for row in rows if row["hybrid"]["score_global"] > row["vector"]["score_global"])
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "protocol": "8 questions, 4 familles (simple, multi-hop, intersection, policy/red-team), scores 0-5",
        "weights": WEIGHTS,
        "aggregates": {
            "vector": vector_aggregate,
            "hybrid": hybrid_aggregate,
            "graph_wins": graph_wins,
            "questions": len(rows),
            "delta": round(hybrid_aggregate["score_global"] - vector_aggregate["score_global"], 2),
        },
        "questions": rows,
    }
    COMPARISON_PATH.parent.mkdir(parents=True, exist_ok=True)
    COMPARISON_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_csv(rows)
    _write_markdown(report)
    return report


def _write_csv(rows: list[dict]) -> Path:
    path = RESULTS_DIR / "comparaison_vector_graph.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["id", "difficulte", "vector_score", "hybrid_score", "delta", "hitl"])
        for row in rows:
            writer.writerow([
                row["id"], row["difficulty"],
                f"{row['vector']['score_global']:.2f}".replace(".", ","),
                f"{row['hybrid']['score_global']:.2f}".replace(".", ","),
                f"{row['delta']:+.2f}".replace(".", ","),
                row["hybrid_hitl"],
            ])
    return path


def _write_markdown(report: dict) -> Path:
    path = RESULTS_DIR / "rapport_comparatif.md"
    aggregates = report["aggregates"]
    lines = [
        "# Rapport comparatif — Vectoriel vs QuantAgent hybride",
        "",
        f"*Généré le {report['generated_at'][:10]} — protocole {report['protocol']}*",
        "",
        "## Résultats globaux (0-5)",
        "",
        "| Métrique | Vectoriel TF-IDF | QuantAgent hybride | Delta |",
        "|---|---:|---:|---:|",
    ]
    for metric in METRICS:
        vector = aggregates["vector"][metric]
        hybrid = aggregates["hybrid"][metric]
        lines.append(f"| {metric} | {vector:.2f} | {hybrid:.2f} | {hybrid - vector:+.2f} |")
    lines.extend([
        "",
        f"**QuantAgent hybride gagne {aggregates['graph_wins']}/{aggregates['questions']} questions** "
        f"avec un score global de {aggregates['hybrid']['score_global']:.2f}/5 contre "
        f"{aggregates['vector']['score_global']:.2f}/5 pour la baseline vectorielle.",
        "",
        "## Détail par question",
        "",
        "| # | Difficulté | Vectoriel | Hybride | Delta | HITL |",
        "|---|---|---:|---:|---:|---|",
    ])
    for row in report["questions"]:
        lines.append(
            f"| {row['id']} | {row['difficulty']} | {row['vector']['score_global']:.2f} | "
            f"{row['hybrid']['score_global']:.2f} | {row['delta']:+.2f} | {row['hybrid_hitl']} |"
        )
    lines.extend([
        "",
        "## Lecture",
        "",
        "La baseline vectorielle retrouve des passages pertinents mais ne calcule pas le P&L, "
        "ne traverse pas les relations portefeuille → position → facteur → politique et ne déclenche pas HITL. "
        "L'agent hybride combine les passages, le graphe et le moteur quantitatif pour produire une réponse chiffrée, "
        "tracée et soumise à validation humaine.",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
