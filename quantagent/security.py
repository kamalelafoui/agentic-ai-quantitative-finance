"""Garde-fous de sécurité : injection, exfiltration, PII, conseil, outils."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .corpus import normalize

PATTERNS: list[tuple[str, str, str, float, str]] = [
    # code, category, regex, severity, policy
    ("INJ-001", "prompt_injection", r"\bignore (toutes )?(les |tes )?instructions?\b", 0.95, "POL-DATA"),
    ("INJ-002", "prompt_injection", r"\bignore (all )?(previous|prior) instructions\b", 0.95, "POL-DATA"),
    ("INJ-003", "prompt_injection", r"\b(prompt systeme|prompt système|system prompt)\b", 0.95, "POL-DATA"),
    ("INJ-004", "jailbreak", r"\b(jailbreak|do anything now|dan mode|mode dan|mode administrateur)\b", 0.90, "POL-DATA"),
    ("INJ-005", "jailbreak", r"\b(tu es maintenant|vous etes maintenant|you are now|act as)\b", 0.75, "POL-DATA"),
    ("INJ-006", "prompt_injection", r"\b(oublie tes regles|oublie les regles|system override|developer message|instructions internes)\b", 0.90, "POL-DATA"),
    ("INJ-007", "prompt_injection", r"\b(ignore|ignorer)\b.{0,20}\b(politique|policy|regle|reglement)\b", 0.85, "POL-DATA"),
    ("EXF-001", "data_exfiltration", r"\bpositions? confidentielles?\b", 0.90, "POL-DATA"),
    ("EXF-002", "data_exfiltration", r"\b(numero de compte|numéro de compte|account number|iban)\b", 0.90, "POL-DATA"),
    ("EXF-003", "data_exfiltration", r"\b(cle api|clé api|api key|secret|token)\b", 0.85, "POL-DATA"),
    ("EXF-004", "data_exfiltration", r"\b(nom du client|nom de client|client name)\b", 0.85, "POL-DATA"),
    ("EXF-005", "data_exfiltration", r"\b(portefeuille|donnees|données) confidentiel(le|les)?\b", 0.85, "POL-DATA"),
    ("EXF-006", "data_exfiltration", r"\b(donne|donne-moi|envoie|affiche|montre)\b.{0,35}\b(positions|portefeuille)\b", 0.85, "POL-DATA"),
    ("TOOL-001", "tool_abuse", r"\b(execute|exécute|run)\b.{0,30}\b(shell|commande|script|code)\b", 0.90, "POL-DATA"),
    ("TOOL-002", "tool_abuse", r"\b(drop table|delete from|rm -rf|sudo)\b", 0.95, "POL-DATA"),
    ("TOOL-003", "tool_abuse", r"\b(curl|wget)\b", 0.70, "POL-DATA"),
    ("PII-001", "pii", r"[\w.+-]+@[\w-]+\.[\w.]+", 0.80, "POL-DATA"),
    ("PII-002", "pii", r"\b(?:\+?\d[\s.-]?){10,}\b", 0.80, "POL-DATA"),
    ("PII-003", "pii", r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b", 0.85, "POL-DATA"),
    ("FIN-001", "financial_advice", r"\b(dois-je|dois je)\b.{0,30}\b(acheter|vendre)\b", 0.75, "POL-CONDUCT"),
    ("FIN-002", "financial_advice", r"\b(conseil personnalise|conseil personnalisé|recommande-moi|recommande moi)\b", 0.75, "POL-CONDUCT"),
    ("FIN-003", "financial_advice", r"\b(garantie? de rendement|rendement assure|rendement assuré|sans risque)\b", 0.80, "POL-CONDUCT"),
    ("FIN-004", "financial_advice", r"\b(quelle action|quel titre)\b.{0,20}\b(acheter|vendre)\b", 0.75, "POL-CONDUCT"),
    ("HRM-001", "harmful", r"\b(blanchiment|blanchir|manipulation de marche|manipulation de marché|manipuler|delit d'initie|délit d'initié)\b", 1.00, "POL-CONDUCT"),
]

MASK_PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[EMAIL_MASQUÉ]"),
    (re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b"), "[IBAN_MASQUÉ]"),
    (re.compile(r"\b(?:\+?\d[\s.-]?){10,}\b"), "[TÉLÉPHONE_MASQUÉ]"),
]


@dataclass
class SecurityResult:
    status: str
    risk_score: float
    flags: list[dict[str, Any]] = field(default_factory=list)
    policy: str = "SEC-GUARD"
    action: str = "allow"
    sanitized_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "risk_score": round(float(self.risk_score), 3),
            "flags": self.flags,
            "policy": self.policy,
            "action": self.action,
            "sanitized_text": self.sanitized_text,
        }


class SecurityGuard:
    def __init__(self):
        self.patterns = [(code, cat, re.compile(regex, re.IGNORECASE), sev, policy) for code, cat, regex, sev, policy in PATTERNS]

    def inspect(self, text: str) -> SecurityResult:
        original = text or ""
        normalized = normalize(original)
        flags: list[dict[str, Any]] = []
        risk = 0.0
        policies: list[str] = []
        for code, category, pattern, severity, policy in self.patterns:
            target = normalized if category not in {"pii"} else original
            match = pattern.search(target)
            if not match:
                continue
            flags.append({
                "code": code,
                "category": category,
                "severity": severity,
                "match": match.group(0)[:120],
                "policy": policy,
            })
            risk = max(risk, severity)
            policies.append(policy)
        if risk >= 0.70:
            status, action = "blocked", "block"
        elif risk >= 0.35:
            status, action = "review", "review"
        else:
            status, action = "allowed", "allow"
        policy = policies[0] if policies else "SEC-GUARD"
        return SecurityResult(
            status=status,
            risk_score=risk,
            flags=flags,
            policy=policy,
            action=action,
            sanitized_text=self.sanitize(original),
        )

    @staticmethod
    def sanitize(text: str) -> str:
        result = text or ""
        for pattern, replacement in MASK_PATTERNS:
            result = pattern.sub(replacement, result)
        return result

    def is_blocked(self, text: str) -> bool:
        return self.inspect(text).status == "blocked"



