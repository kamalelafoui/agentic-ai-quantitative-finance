"""Moteur de politique HITL et journalisation des décisions humaines."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import HITL_LOG_PATH

APPROVAL_CATALOG = {
    "HITL-RISK": {
        "id": "HITL-RISK",
        "role": "Risk Manager",
        "label": "Validation Risk",
        "sla_hours": 4,
        "scope": "Dépassement de limite de marché, perte scénario, concentration",
    },
    "HITL-IC": {
        "id": "HITL-IC",
        "role": "Comité d'Investissement",
        "label": "Validation Comité d'Investissement",
        "sla_hours": 24,
        "scope": "Opération de portefeuille > 2,5 % de la NAV",
    },
    "HITL-COMPLIANCE": {
        "id": "HITL-COMPLIANCE",
        "role": "Compliance Officer",
        "label": "Validation Compliance",
        "sla_hours": 24,
        "scope": "Communication client, ESG, données personnelles, watchlist",
    },
    "HITL-MODEL": {
        "id": "HITL-MODEL",
        "role": "Model Risk Officer",
        "label": "Validation Model Risk",
        "sla_hours": 48,
        "scope": "Changement de modèle ou de paramètre de calibration",
    },
}


def _approval(approval_id: str, reason: str) -> dict[str, Any]:
    item = dict(APPROVAL_CATALOG[approval_id])
    item["reason"] = reason
    item["status"] = "PENDING"
    return item


class PolicyEngine:
    def evaluate(
        self,
        intent: str,
        quant: dict | None,
        security: dict,
        question: str,
    ) -> dict[str, Any]:
        if security.get("status") == "blocked":
            return {
                "required": True,
                "status": "BLOCKED",
                "approvals": [],
                "rationale": "Requête bloquée par le filtre de sécurité : aucune décision humaine n'est engagée, l'événement est escaladé à AI Security et au DPO.",
                "conditions": ["Ne pas exécuter la requête", "Journaliser l'événement", "Notifier AI Security"],
                "next_step": "Revue sécurité sous 1 heure",
                "decision_options": [],
            }

        normalized = question.lower()
        approvals: list[dict[str, Any]] = []
        conditions: list[str] = []
        rationale = "Aucune approbation HITL requise pour une simple lecture d'analyse."
        status = "NOT_REQUIRED"
        next_step = "Lecture autorisée, aucune exécution d'ordre."

        breach = bool(quant and quant.get("breaches"))
        impact_pct = abs(float(quant.get("impact_pct_nav", 0.0))) if quant else 0.0
        is_trade = any(word in normalized for word in ["réduire", "reduire", "vendre", "vente", "achat", "opération", "operation", "rebalancement"])
        esg = intent == "esg" or "esg" in normalized or "watchlist" in normalized or "vonovia" in normalized or "edf" in normalized

        if intent in {"scenario", "limits", "credit"} and (breach or impact_pct > 2.5):
            status = "PENDING_APPROVAL"
            rationale = (
                "Le scénario dépasse la limite de perte de 3,0 % NAV ou l'impact potentiel excède 2,5 % NAV. "
                "La procédure POL-HITL exige une validation Risk avant toute action."
            )
            approvals.append(_approval("HITL-RISK", "Dépassement de la limite CTL-SCENARIO-LOSS / impact > 2,5 % NAV."))
            if is_trade or impact_pct > 2.5:
                approvals.append(_approval("HITL-IC", "Opération de portefeuille significative (> 2,5 % NAV)."))
                conditions.append("Présenter une proposition chiffrée au Comité d'Investissement.")
            if esg:
                approvals.append(_approval("HITL-COMPLIANCE", "Communication ou opération sur un émetteur de la watchlist ESG."))
            conditions.extend([
                "Ne pas exécuter d'ordre : le agent prépare seulement le dossier.",
                "Documenter les hypothèses, les sources et les chemins de preuve.",
            ])
            next_step = "Décision Risk sous 4 h, puis Comité d'Investissement sous 24 h."
        elif intent == "approval":
            status = "PENDING_APPROVAL"
            rationale = (
                "Une réduction de la poche obligataire est une opération de portefeuille qui dépasse 2,5 % NAV "
                "et intervient après un dépassement de limite."
            )
            approvals.append(_approval("HITL-RISK", "Vérifier l'impact risque et la conformité aux limites."))
            approvals.append(_approval("HITL-IC", "Valider l'opération de réduction de la poche obligataire."))
            if esg:
                approvals.append(_approval("HITL-COMPLIANCE", "Vérifier la watchlist ESG (Vonovia, EDF) et la communication."))
            conditions.extend([
                "La réduction de 10 % ne suffit pas : viser au moins 18,2 %, soit 20 % avec marge.",
                "Vérifier le ratio de liquidité T+1 après l'opération.",
                "Journaliser la décision et la justification.",
            ])
            next_step = "Dossier HITL à soumettre au Risk puis au Comité d'Investissement."
        elif intent == "esg":
            status = "PENDING_APPROVAL"
            rationale = "La question porte sur la watchlist ESG : une revue Compliance est requise avant toute communication."
            approvals.append(_approval("HITL-COMPLIANCE", "Vérifier la watchlist ESG et le caractère non-exclusif des émetteurs."))
            conditions.append("Mentionner explicitement que la watchlist n'est pas une exclusion.")
            next_step = "Validation Compliance sous 24 h."
        elif intent == "data_policy":
            status = "PENDING_APPROVAL"
            rationale = "La demande concerne des données personnelles ou confidentielles : blocage et escalade DPO/Compliance."
            approvals.append(_approval("HITL-COMPLIANCE", "Revue DPO / Compliance sur les données personnelles."))
            conditions.extend([
                "Ne jamais afficher le nom du client, le numéro de compte, l'IBAN ou l'email.",
                "Masquer toute PII avant sortie.",
            ])
            next_step = "Escalade DPO sous 1 h, aucune donnée affichée."
        elif intent == "metrics":
            rationale = "Indicateurs de risque agrégés, sans opération ni donnée personnelle."
            next_step = "Lecture autorisée."
        elif intent == "general":
            rationale = "Réponse informative agrégée, sans exécution d'ordre."
            next_step = "Lecture autorisée avec avertissement."

        return {
            "required": status != "NOT_REQUIRED",
            "status": status,
            "approvals": approvals,
            "rationale": rationale,
            "conditions": conditions,
            "next_step": next_step,
            "decision_options": ["APPROUVER", "REJETER", "ESCALADER"] if status == "PENDING_APPROVAL" else [],
        }

    @staticmethod
    def log_decision(
        request_id: str,
        reviewer: str,
        decision: str,
        comment: str = "",
        path: Path | None = None,
    ) -> dict[str, Any]:
        decision = decision.upper().strip()
        if decision not in {"APPROUVER", "REJETER", "ESCALADER"}:
            raise ValueError("Décision invalide : APPROUVER, REJETER ou ESCALADER.")
        record = {
            "decision_id": f"HITL-{uuid.uuid4().hex[:8].upper()}",
            "request_id": request_id,
            "reviewer": reviewer.strip() or "reviewer-anonyme",
            "decision": decision,
            "comment": comment.strip(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": "SIMULATION",
        }
        log_path = path or HITL_LOG_PATH
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record
