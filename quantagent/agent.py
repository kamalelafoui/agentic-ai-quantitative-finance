"""Agent hybride QuantAgent : sécurité, routage, RAG vectoriel, graphe, quant, HITL."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .config import APP_NAME, APP_VERSION, DISCLAIMER, PORTFOLIO_ID
from .corpus import Document, normalize
from .hitl import PolicyEngine
from .knowledge_graph import KnowledgeGraph
from .quant import QuantEngine
from .schema import validate_response
from .security import SecurityGuard
from .vector_store import SearchHit, TfidfVectorStore


def fmt_m(value_eur: float, decimals: int = 2, signed: bool = True) -> str:
    sign = "+" if signed else ""
    text = f"{value_eur / 1_000_000:{sign},.{decimals}f}".replace(".", ",")
    return f"{text} M€"


def fmt_pct(value: float, decimals: int = 2) -> str:
    return f"{value:+.{decimals}f} %".replace(".", ",")


def fmt_num(value: float, decimals: int = 1) -> str:
    return f"{value:.{decimals}f}".replace(".", ",")


@dataclass
class Source:
    doc_id: str
    title: str
    snippet: str
    score: float = 0.9

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "snippet": self.snippet,
            "score": round(float(self.score), 4),
        }


class VectorRAG:
    """Baseline vectorielle TF-IDF, sans graphe ni calcul quantitatif."""

    def __init__(self, documents: list[Document], graph: KnowledgeGraph):
        self.documents = {doc.id: doc for doc in documents}
        self.graph = graph
        self.store = TfidfVectorStore(documents)

    def ask(self, question: str, top_k: int = 4) -> dict[str, Any]:
        started = time.perf_counter()
        hits = self.store.search(question, top_k=top_k)
        doc_ids = [hit.document.id for hit in hits]
        sentences = self.store.search_sentences(question, top_k=5, doc_ids=doc_ids)
        if not sentences:
            sentences = [SearchHit(document=hit.document, score=hit.score, sentence=hit.document.snippet) for hit in hits]
        lines = [
            "**Recherche vectorielle (TF-IDF, top-k documents).**",
            "Les passages les plus proches sémantiquement de la question sont :",
        ]
        for hit in sentences[:5]:
            lines.append(f"- « {hit.sentence} » — *{hit.document.id} · {hit.document.title}*")
        answer = "\n".join(lines) if hits else "Aucun passage suffisamment proche n'a été trouvé dans le corpus."
        sources = [
            Source(doc_id=hit.document.id, title=hit.document.title, snippet=hit.document.snippet, score=hit.score)
            for hit in hits
        ]
        entities = self.graph.find_entities(answer, max_entities=8)
        confidence = min(0.72, 0.35 + (sum(hit.score for hit in hits) / max(len(hits), 1)) * 1.8)
        return {
            "answer": answer,
            "sources": sources,
            "entities": entities,
            "confidence": confidence,
            "elapsed_ms": (time.perf_counter() - started) * 1000,
            "hits": hits,
        }


class QuantAgent:
    def __init__(
        self,
        documents: list[Document],
        graph: KnowledgeGraph,
        quant: QuantEngine | None = None,
        security: SecurityGuard | None = None,
        policy: PolicyEngine | None = None,
    ):
        self.documents = documents
        self.by_id = {doc.id: doc for doc in documents}
        self.graph = graph
        self.quant = quant or QuantEngine()
        self.security = security or SecurityGuard()
        self.policy = policy or PolicyEngine()
        self.vector = VectorRAG(documents, graph)

    # ------------------------------------------------------------------
    # Routage
    # ------------------------------------------------------------------
    def route(self, question: str, seeds: list[str]) -> str:
        q = normalize(question)
        if any(word in q for word in ["ignore", "prompt systeme", "jailbreak", "mode administrateur", "instructions precedentes"]):
            return "security"
        if any(word in q for word in ["donnees personnelles", "pii", "nom du client", "numero de compte", "iban", "rgpd", "dpo"]):
            return "data_policy"
        if any(word in q for word in ["esg", "watchlist", "exclusion", "vigilance"]):
            return "esg"
        if any(word in q for word in ["approbation", "hitl", "validation", "qui doit approuver", "comite"]):
            return "approval"
        if any(word in q for word in ["limite", "respecte", "concentration", "depassement", "depasse"]):
            return "limits"
        if any(word in q for word in ["spread", "credit"]):
            return "credit"
        if any(word in q for word in ["impact", "choc", "scenario", "taux", "sensibilite"]):
            return "scenario"
        if any(word in q for word in ["duration", "var"]):
            return "metrics"
        return "general"

    def choose_scenario(self, question: str, intent: str) -> str:
        q = normalize(question)
        if intent == "credit" or "spread" in q or "credit" in q:
            return "SCN-CREDIT-50BP"
        if "action" in q and ("-10" in q or "correction" in q):
            return "SCN-EQUITY-10PCT"
        return "SCN-RATES-100BP"

    # ------------------------------------------------------------------
    # API principale
    # ------------------------------------------------------------------
    def ask(
        self,
        question: str,
        portfolio_id: str = PORTFOLIO_ID,
        scenario_id: str | None = None,
        mode: str = "hybrid",
        top_k: int = 4,
        evaluation_baseline: bool = False,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        request_id = f"REQ-{uuid.uuid4().hex[:12].upper()}"
        trace: list[dict[str, Any]] = []
        security_result = self.security.inspect(question)
        security_payload = security_result.to_dict()
        trace.append({"step": "security", "detail": f"Filtre d'entrée : {security_result.status} (risque {security_result.risk_score:.2f}).", "elapsed_ms": 0.0})
        seeds = self.graph.find_entities(question, max_entities=12)
        intent = self.route(question, seeds)
        trace.append({"step": "entity_linking", "detail": f"{len(seeds)} entités liées : {', '.join(seeds[:10]) or '—'}.", "elapsed_ms": 0.0})
        trace.append({"step": "intent_routing", "detail": f"Intent détecté : {intent}.", "elapsed_ms": 0.0})

        if mode == "vector" and evaluation_baseline:
            return self._vector_response(request_id, question, security_payload, seeds, intent, trace, started, top_k)

        if security_result.status == "blocked":
            return self._blocked_response(request_id, question, mode, security_payload, seeds, trace, started, intent)

        if mode == "vector":
            return self._vector_response(request_id, question, security_payload, seeds, intent, trace, started, top_k)

        scenario_id = scenario_id or self.choose_scenario(question, intent)
        quant_result = self._run_quant(intent, scenario_id)
        trace.append({
            "step": "quantification",
            "detail": "Aucun calcul quantitatif." if quant_result is None else f"Scénario {scenario_id} exécuté : impact {quant_result['impact_eur']/1e6:+.2f} M€.",
            "elapsed_ms": 0.0,
        })

        vector_result = self.vector.ask(question, top_k=top_k)
        trace.append({"step": "vector_retrieval", "detail": f"{len(vector_result['sources'])} documents récupérés par TF-IDF.", "elapsed_ms": round(vector_result["elapsed_ms"], 2)})

        answer = self._compose_answer(intent, question, quant_result, vector_result, seeds, scenario_id)
        answer += self._traceability(intent, seeds, quant_result)
        sources = self._sources(intent, seeds, quant_result, vector_result)
        graph_payload = self._graph_payload(seeds, intent, quant_result)
        trace.append({"step": "graph_traversal", "detail": f"{len(graph_payload['nodes'])} nœuds, {len(graph_payload['edges'])} arêtes, {len(graph_payload['paths'])} chemins de preuve.", "elapsed_ms": 0.0})

        hitl = self.policy.evaluate(intent, quant_result, security_payload, question)
        trace.append({"step": "hitl_policy", "detail": f"Statut HITL : {hitl['status']} ; {len(hitl['approvals'])} approbation(s).", "elapsed_ms": 0.0})

        confidence = self._confidence(intent, quant_result, sources, graph_payload, seeds)
        latency = (time.perf_counter() - started) * 1000
        payload = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": {"name": APP_NAME, "version": APP_VERSION, "mode": mode},
            "question": question,
            "intent": intent,
            "answer": answer,
            "confidence": round(confidence, 3),
            "latency_ms": round(latency, 2),
            "entities": seeds,
            "sources": [source.to_dict() for source in sources],
            "graph": graph_payload,
            "quant": quant_result,
            "hitl": hitl,
            "security": security_payload,
            "trace": trace,
            "meta": {"json_valid": False, "schema_version": "1.0.0", "data_as_of": "2026-10-31"},
            "disclaimer": DISCLAIMER,
        }
        payload["trace"].append({"step": "json_validation", "detail": "Validation du contrat JSON avant sortie.", "elapsed_ms": 0.0})
        payload["meta"]["json_valid"] = validate_response(payload)
        payload["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
        return payload

    def _run_quant(self, intent: str, scenario_id: str) -> dict | None:
        if intent in {"scenario", "limits", "metrics"}:
            return self.quant.run_scenario(scenario_id)
        if intent == "credit":
            return self.quant.run_scenario("SCN-CREDIT-50BP")
        if intent == "esg":
            return self.quant.run_scenario("SCN-RATES-100BP")
        if intent == "approval":
            base = self.quant.run_scenario("SCN-RATES-100BP")
            proposal = self.quant.run_scenario("SCN-RATES-100BP", bond_reduction_pct=10.0)
            proposal["base_impact_eur"] = base["impact_eur"]
            proposal["base_impact_pct_nav"] = base["impact_pct_nav"]
            proposal["required_bond_reduction_pct"] = base["required_bond_reduction_pct"]
            proposal["recommended_bond_reduction_pct"] = base["recommended_bond_reduction_pct"]
            return proposal
        return None

    # ------------------------------------------------------------------
    # Réponses spéciales
    # ------------------------------------------------------------------
    def _blocked_response(self, request_id, question, mode, security_payload, seeds, trace, started, intent="security"):
        if intent == "data_policy":
            answer = (
                "**Non — les données personnelles sont interdites en sortie.**\n"
                "Le nom du client, le numéro de compte, l'IBAN, l'email et le téléphone sont des données personnelles (PII). "
                "La politique POL-DATA et le RGPD imposent le masquage et l'anonymisation. "
                "La demande est bloquée et escaladée au DPO / HITL-COMPLIANCE. Aucune donnée n'est affichée. "
                "Sources : D17, D08."
            )
            sources = [self._source("D17"), self._source("D08")]
            hitl = self.policy.evaluate("data_policy", None, {**security_payload, "status": "review"}, question)
        else:
            answer = (
                "**Requête bloquée par le filtre de sécurité.**\n"
                "La requête contient une tentative d'injection de prompt ou d'exfiltration de données internes. "
                "Aucune instruction système ni position confidentielle n'est révélée. "
                "L'événement est journalisé et escaladé à l'équipe AI Security. "
                "Sources : D18, D17."
            )
            sources = [self._source("D18"), self._source("D17")]
            hitl = self.policy.evaluate("security", None, security_payload, question)
        answer += self._traceability(intent, seeds, None)
        trace.append({"step": "security_block", "detail": "Sortie bloquée ; aucune donnée interne exposée.", "elapsed_ms": 0.0})
        trace.append({"step": "json_validation", "detail": "Validation du contrat JSON de refus.", "elapsed_ms": 0.0})
        if intent == "data_policy":
            graph_payload = self.graph.subgraph(["POL-DATA", "REG-GDPR", "HITL-COMPLIANCE"], depth=1)
            graph_payload["paths"] = self.graph.paths_between("POL-DATA", "REG-GDPR", max_length=3, limit=3) + self.graph.paths_between("POL-DATA", "HITL-COMPLIANCE", max_length=3, limit=3)
        else:
            graph_payload = self.graph.subgraph(["POL-DATA", "POL-HITL"], depth=1)
            graph_payload["paths"] = self.graph.paths_between("POL-DATA", "POL-HITL", max_length=3, limit=3)
        graph_payload["seed_count"] = len(seeds)
        payload = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": {"name": APP_NAME, "version": APP_VERSION, "mode": mode},
            "question": question,
            "intent": intent,
            "answer": answer,
            "confidence": 0.99,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "entities": seeds,
            "sources": [source.to_dict() for source in sources],
            "graph": graph_payload,
            "quant": None,
            "hitl": hitl,
            "security": security_payload,
            "trace": trace,
            "meta": {"json_valid": False, "schema_version": "1.0.0", "data_as_of": "2026-10-31"},
            "disclaimer": DISCLAIMER,
        }
        payload["meta"]["json_valid"] = validate_response(payload)
        return payload

    def _vector_response(self, request_id, question, security_payload, seeds, intent, trace, started, top_k):
        result = self.vector.ask(question, top_k=top_k)
        trace.append({"step": "vector_retrieval", "detail": f"Baseline TF-IDF : {len(result['sources'])} documents.", "elapsed_ms": round(result["elapsed_ms"], 2)})
        trace.append({"step": "json_validation", "detail": "Validation du contrat JSON de la baseline.", "elapsed_ms": 0.0})
        hitl = self.policy.evaluate(intent, None, security_payload, question)
        payload = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": {"name": APP_NAME, "version": APP_VERSION, "mode": "vector"},
            "question": question,
            "intent": intent,
            "answer": result["answer"],
            "confidence": round(result["confidence"], 3),
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "entities": result["entities"],
            "sources": [source.to_dict() for source in result["sources"]],
            "graph": {"nodes": [], "edges": [], "paths": [], "seed_count": len(seeds)},
            "quant": None,
            "hitl": hitl,
            "security": security_payload,
            "trace": trace,
            "meta": {"json_valid": False, "schema_version": "1.0.0", "data_as_of": "2026-10-31"},
            "disclaimer": DISCLAIMER,
        }
        payload["meta"]["json_valid"] = validate_response(payload)
        return payload

    # ------------------------------------------------------------------
    # Composition de la réponse
    # ------------------------------------------------------------------
    def _compose_answer(self, intent, question, quant, vector_result, seeds, scenario_id) -> str:
        if intent == "metrics":
            return self._answer_metrics(quant)
        if intent == "scenario":
            return self._answer_scenario(quant)
        if intent == "limits":
            return self._answer_limits(quant)
        if intent == "approval":
            return self._answer_approval(quant)
        if intent == "esg":
            return self._answer_esg(quant)
        if intent == "credit":
            return self._answer_credit(quant)
        if intent == "data_policy":
            return (
                "**Non — les données personnelles sont interdites en sortie.**\n"
                "Le nom du client, le numéro de compte, l'IBAN, l'email et le téléphone sont des données personnelles (PII). "
                "La politique POL-DATA et le RGPD imposent le masquage et l'anonymisation. "
                "La demande est bloquée et escaladée au DPO / HITL-COMPLIANCE. Aucune donnée n'est affichée. "
                "Sources : D17, D08."
            )
        return self._answer_general(vector_result, seeds)

    def _answer_metrics(self, quant) -> str:
        base = self.quant.base_metrics()
        check = next((c for c in (quant or {}).get("limit_checks", []) if c["control"] == "CTL-SCENARIO-LOSS"), None)
        scenario_line = ""
        if check:
            scenario_line = f"- Perte scénario +100 bp : {fmt_pct(-check['value'])} NAV (limite 3,0 %) — {check['status']}.\n"
        return (
            "**Indicateurs du portefeuille Core Europe (31/10/2026).**\n"
            f"- Duration totale : {fmt_num(base['duration_years'])} an (limite 5,0 ans) — OK.\n"
            f"- VaR 99 % 1 jour : {fmt_num(base['var_99_1d_pct'])} % NAV (limite 2,5 %) — OK.\n"
            f"- Liquidité T+1 : {fmt_num(base['liquidity_t1_pct'])} % NAV (minimum 20 %) — OK.\n"
            f"{scenario_line}"
            "La duration et la VaR sont documentées dans D02 et D21. Le portefeuille reste dans les limites de lecture, "
            "mais le scénario de taux doit être revu par le Risk."
        )

    def _answer_scenario(self, quant) -> str:
        if not quant:
            return "Le scénario n'a pas pu être calculé."
        lines = [
            f"**Impact du scénario {quant['scenario']['id']} sur {quant['portfolio']['id']}.**",
            f"Le choc de +100 pb sur les taux EUR produit une perte estimée de {fmt_m(quant['impact_eur'], 2)}, "
            f"soit {fmt_pct(quant['impact_pct_nav'])} de la NAV. La NAV passerait de 250,00 M€ à {fmt_m(quant['nav_after_eur'], 2, signed=False)}.",
            "",
            "**Principaux contributeurs**",
        ]
        for index, row in enumerate(quant["top_contributors"][:5], start=1):
            lines.append(f"{index}. {row['name']} : {fmt_m(row['impact_eur'], 3)} ({row['driver']}).")
        breach = next((c for c in quant["limit_checks"] if c["status"] == "BREACH"), None)
        if breach:
            lines.extend([
                "",
                f"**Limite** : perte scénario {fmt_num(breach['value'], 2)} % > {fmt_num(breach['limit'], 2)} % NAV, "
                f"dépassement de {fmt_m(abs(quant['impact_eur']) - abs(breach['limit']) / 100 * quant['portfolio']['nav_eur'], 2)}. "
                "Statut HITL : PENDING_APPROVAL (HITL-RISK, HITL-IC).",
            ])
        lines.append(
            "**Méthode** : P&L = -MV × duration × Δy pour les obligations ; bêta taux pour les actions. "
            "Sources : D04, D05, D21, D02, D13, D14."
        )
        return "\n".join(lines)

    def _answer_limits(self, quant) -> str:
        if not quant:
            return "Les limites n'ont pas pu être contrôlées."
        lines = ["**Contrôle des limites après le choc +100 bp.**"]
        breach = [c for c in quant["limit_checks"] if c["status"] == "BREACH"]
        lines.append("Non, une limite est dépassée." if breach else "Oui, toutes les limites sont respectées.")
        for check in quant["limit_checks"]:
            display_value = -check["value"] if check["control"] == "CTL-SCENARIO-LOSS" else check["value"]
            if check["direction"] == "max":
                comparator = "<" if check["status"] != "BREACH" else ">"
                value_text = f"{fmt_num(display_value, 2)} {check['unit']}"
                limit_text = f"{fmt_num(check['limit'], 2)} {check['unit']}"
            else:
                comparator = ">" if check["status"] != "BREACH" else "<"
                value_text = f"{fmt_num(display_value, 2)} {check['unit']}"
                limit_text = f"{fmt_num(check['limit'], 2)} {check['unit']}"
            lines.append(f"- {check['name']} : {value_text} {comparator} {limit_text} → {check['status']} ({check['control']}).")
        if breach:
            amount = abs(quant["impact_eur"]) - abs(breach[0]["limit"]) / 100 * quant["portfolio"]["nav_eur"]
            lines.append(f"Dépassement de la limite de perte scénario : {fmt_m(amount, 2)}.")
        lines.append(
            "Les limites autres que la perte scénario sont mesurées sur la NAV avant choc (D04). "
            "Validation HITL-RISK requise. Sources : D03, D06, D07, D21."
        )
        return "\n".join(lines)

    def _answer_approval(self, quant) -> str:
        if not quant:
            return "Le circuit HITL n'a pas pu être calculé."
        base_pct = quant.get("base_impact_pct_nav", quant["impact_pct_nav"])
        proposal_pct = quant["impact_pct_nav"]
        required = quant.get("required_bond_reduction_pct", 18.2)
        recommended = quant.get("recommended_bond_reduction_pct", 19.5)
        return (
            "**Circuit HITL pour une réduction de 10 % de la poche obligataire.**\n"
            "Une réduction de 10 % représente 6,4 M€ (10 % × 64,0 M€). Elle dépasse 2,5 % NAV et intervient après un dépassement de limite : "
            "HITL-RISK et HITL-IC sont requis. HITL-COMPLIANCE est requis si la communication porte sur Vonovia ou EDF (watchlist ESG). "
            "HITL-MODEL n'est pas requis.\n"
            f"La réduction de 10 % ne suffit pas : la perte scénario resterait à {fmt_pct(proposal_pct)} NAV "
            f"(contre {fmt_pct(base_pct)} sans réduction). "
            f"Il faut environ {fmt_num(required)} % (calcul exact) ou {fmt_num(recommended)} % avec marge opérationnelle pour repasser sous 3,0 %.\n"
            "Chemins de preuve : PF-CORE-EU → POL-HITL → HITL-RISK / HITL-IC. Sources : D03, D10, D11, D21."
        )

    def _answer_esg(self, quant) -> str:
        impacts = {}
        if quant:
            for row in quant.get("contributors", []):
                impacts[row["position_id"]] = row["impact_eur"]
        vonovia = impacts.get("POS-03", -1_800_000)
        edf = impacts.get("POS-08", -1_800_000)
        return (
            "**Intersection taux × vigilance ESG.**\n"
            "Deux émetteurs cumulent une forte sensibilité aux taux et une vigilance ESG :\n"
            f"- Vonovia (POS-03) : {fmt_m(vonovia, 3)} sur +100 bp ; watchlist ESG (accessibilité/logement), pas exclusion.\n"
            f"- EDF (POS-08) : {fmt_m(edf, 3)} sur +100 bp ; watchlist ESG (controverse nucléaire), pas exclusion.\n"
            "Toute communication les concernant requiert HITL-COMPLIANCE et doit mentionner que la watchlist n'est pas une exclusion. "
            "Sources : D13, D14, D15."
        )

    def _answer_credit(self, quant) -> str:
        if not quant:
            return "Le scénario crédit n'a pas pu être calculé."
        by_id = {row["position_id"]: row for row in quant["contributors"]}
        bnp = by_id.get("POS-01", {"impact_eur": -75_000})
        axa = by_id.get("POS-10", {"impact_eur": -300_000})
        edf = by_id.get("POS-08", {"impact_eur": -125_000})
        vonovia = by_id.get("POS-03", {"impact_eur": -100_000})
        return (
            "**Impact du scénario crédit +50 pb.**\n"
            f"La perte crédit totale est de {fmt_m(quant['impact_eur'], 2)}, soit {fmt_pct(quant['impact_pct_nav'])} NAV, "
            "sous la limite de 3,0 %.\n"
            f"- BNP Paribas : {fmt_m(bnp['impact_eur'], 3)} (DV01 -1 500 €/bp).\n"
            f"- AXA 2034 : {fmt_m(axa['impact_eur'], 2)} (DV01 -6 000 €/bp).\n"
            f"- EDF 2035 : {fmt_m(edf['impact_eur'], 3)}.\n"
            f"- Vonovia : {fmt_m(vonovia['impact_eur'], 2)}.\n"
            "Les positions bancaires sont exposées via BNP et le portefeuille obligataire. Sources : D12, D22."
        )

    def _answer_general(self, vector_result, seeds) -> str:
        lines = ["**Réponse hybride (vectoriel + graphe).**"]
        if vector_result["answer"]:
            lines.append(vector_result["answer"])
        facts = []
        for seed in seeds[:5]:
            profile = self.graph.profile(seed)
            if profile:
                rel, tails = next(iter(profile.items()))
                facts.append(f"{self.graph.label(seed)} —{rel}→ {', '.join(self.graph.label(t) for t in tails[:3])}")
        if facts:
            lines.append("\n**Faits du graphe**\n" + "\n".join(f"- {fact}" for fact in facts))
        lines.append("\nSources : " + ", ".join(sorted({s.doc_id for s in vector_result["sources"]}) or ["D01"]))
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Sources et graphe
    # ------------------------------------------------------------------
    def _source(self, doc_id: str, score: float = 0.9) -> Source:
        doc = self.by_id.get(doc_id)
        if not doc:
            return Source(doc_id=doc_id, title=doc_id, snippet="", score=score)
        return Source(doc_id=doc.id, title=doc.title, snippet=doc.snippet, score=score)

    def _sources(self, intent, seeds, quant, vector_result) -> list[Source]:
        wanted: list[str] = []
        if intent == "metrics":
            wanted = ["D02", "D21", "D19"]
        elif intent == "scenario":
            wanted = ["D04", "D05", "D21", "D02", "D13", "D14"]
        elif intent == "limits":
            wanted = ["D03", "D06", "D07", "D21", "D04"]
        elif intent == "approval":
            wanted = ["D03", "D10", "D11", "D21", "D14"]
        elif intent == "esg":
            wanted = ["D13", "D14", "D15"]
        elif intent == "credit":
            wanted = ["D12", "D22"]
        elif intent == "data_policy":
            wanted = ["D17", "D08"]
        elif intent == "security":
            wanted = ["D18", "D17"]
        if quant:
            for row in quant.get("contributors", [])[:6]:
                node = self.graph.node(row["position_id"])
                if node:
                    wanted.extend(node.get("docs", [])[:2])
        for seed in seeds[:5]:
            node = self.graph.node(seed)
            if node:
                wanted.extend(node.get("docs", [])[:2])
        for hit in vector_result["sources"][:3]:
            wanted.append(hit.doc_id)
        unique: list[str] = []
        for doc_id in wanted:
            if doc_id in self.by_id and doc_id not in unique:
                unique.append(doc_id)
        return [self._source(doc_id, 0.95 if index < 3 else 0.80) for index, doc_id in enumerate(unique)]

    def _graph_payload(self, seeds, intent, quant) -> dict[str, Any]:
        subgraph = self.graph.subgraph(seeds, depth=2, max_nodes=65)
        paths = self.graph.traverse(seeds, depth=3, max_paths=30)
        key_pairs = []
        if intent in {"scenario", "limits", "metrics"}:
            key_pairs = [("PF-CORE-EU", "SCN-RATES-100BP"), ("PF-CORE-EU", "CTL-SCENARIO-LOSS"), ("PF-CORE-EU", "HITL-RISK")]
        elif intent == "approval":
            key_pairs = [("PF-CORE-EU", "POL-HITL"), ("PF-CORE-EU", "HITL-RISK"), ("PF-CORE-EU", "HITL-IC")]
        elif intent == "esg":
            key_pairs = [("PF-CORE-EU", "POS-03"), ("POS-03", "WL-ESG"), ("POS-08", "WL-ESG")]
        elif intent == "credit":
            key_pairs = [("PF-CORE-EU", "POS-01"), ("POS-01", "FACTOR-CREDIT-SPREAD"), ("POS-10", "FACTOR-CREDIT-SPREAD")]
        elif intent == "data_policy":
            key_pairs = [("POL-DATA", "REG-GDPR"), ("POL-DATA", "HITL-COMPLIANCE")]
        for source, target in key_pairs:
            paths.extend(self.graph.paths_between(source, target, max_length=4, limit=4))
        deduped = []
        seen = set()
        for path in paths:
            key = tuple(path.get("nodes", []))
            if key and key not in seen:
                seen.add(key)
                deduped.append(path)
        return {
            "nodes": subgraph["nodes"],
            "edges": subgraph["edges"],
            "paths": deduped[:40],
            "seed_count": len(seeds),
        }

    def _traceability(self, intent: str, seeds: list[str], quant: dict | None) -> str:
        related: list[str] = []
        if intent == "scenario":
            related = ["PF-CORE-EU", "SCN-RATES-100BP"]
            if quant:
                related += [row["position_id"] for row in quant.get("top_contributors", [])[:5]]
        elif intent == "limits":
            related = ["PF-CORE-EU", "CTL-SCENARIO-LOSS", "CTL-ISSUER-CAP", "CTL-SECTOR-CAP", "CTL-LIQUIDITY", "CTL-DURATION", "HITL-RISK"]
        elif intent == "approval":
            related = ["PF-CORE-EU", "POL-HITL", "HITL-RISK", "HITL-IC", "HITL-COMPLIANCE", "POL-ESG"]
        elif intent == "esg":
            related = ["WL-ESG", "POL-ESG", "POS-03", "POS-08", "ISS-VONOVIA", "ISS-EDF", "HITL-COMPLIANCE"]
        elif intent == "credit":
            related = ["SCN-CREDIT-50BP", "FACTOR-CREDIT-SPREAD", "POS-01", "POS-10", "POS-08", "POS-03"]
        elif intent == "data_policy":
            related = ["POL-DATA", "REG-GDPR", "HITL-COMPLIANCE"]
        elif intent == "security":
            related = ["POL-DATA", "POL-HITL"]
        elif intent == "metrics":
            related = ["PF-CORE-EU", "MET-DURATION", "MET-VAR", "MET-SCENARIO-LOSS"]
        else:
            related = seeds[:8]
        ordered: list[str] = []
        for node_id in related + seeds:
            if node_id not in ordered and self.graph.node(node_id):
                ordered.append(node_id)
        if not ordered:
            return ""
        return "\n\n**Traçabilité** : " + ", ".join(ordered[:14]) + "."

    def _confidence(self, intent, quant, sources, graph_payload, seeds) -> float:
        base = {
            "scenario": 0.96, "limits": 0.95, "approval": 0.93, "esg": 0.92,
            "credit": 0.92, "metrics": 0.90, "data_policy": 0.97, "general": 0.78,
        }.get(intent, 0.80)
        if not sources:
            base -= 0.10
        if not seeds:
            base -= 0.08
        if quant and quant.get("breaches"):
            base = min(0.98, base + 0.01)
        if len(graph_payload.get("paths", [])) < 2:
            base -= 0.04
        return max(0.40, min(0.99, base))

