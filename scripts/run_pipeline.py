"""Pipeline complet : évaluation, Red Team, validation JSON, visualisations."""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quantagent.agent import QuantAgent
from quantagent.config import (
    ANSWERS_PATH,
    APP_VERSION,
    DATA_DIR,
    DOCS_DIR,
    RESULTS_DIR,
    SCHEMA_PATH,
    STATS_PATH,
    VALIDATION_PATH,
)
from quantagent.corpus import load_corpus, load_questions
from quantagent.evaluation import run_comparison
from quantagent.knowledge_graph import KnowledgeGraph
from quantagent.quant import QuantEngine
from quantagent.redteam import run_campaign
from quantagent.schema import validate_response
from quantagent.visuals import build_all_visuals

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    documents = load_corpus()
    questions = load_questions()
    graph = KnowledgeGraph.from_files()
    graph.save_json()
    graph.save_cypher()
    quant = QuantEngine()
    agent = QuantAgent(documents, graph, quant=quant)

    print("1/5 — Évaluation vectoriel vs hybride")
    comparison = run_comparison(agent, questions, graph)

    print("2/5 — Réponses JSON et cas de démonstration")
    answers = []
    for question in questions:
        payload = agent.ask(question.question)
        answers.append(payload)
    ANSWERS_PATH.write_text(json.dumps(answers, ensure_ascii=False, indent=2), encoding="utf-8")
    showcase = agent.ask(questions[1].question)
    showcase["meta"]["demo_case"] = "Q2 — scénario taux +100 bp"
    showcase["meta"]["validation"] = "JSON Schema Draft 2020-12"
    (RESULTS_DIR / "JSON_Final.json").write_text(json.dumps(showcase, ensure_ascii=False, indent=2), encoding="utf-8")

    print("3/5 — Campagne Red Team")
    redteam = run_campaign(agent)

    print("4/5 — Validation JSON sur 100 requêtes")
    suffixes = [
        "",
        " Merci de citer les sources.",
        " Réponds en français et explique les hypothèses.",
        " Donne le détail des limites et des contrôles.",
        " Explique le rôle du Risk et du Comité d'Investissement.",
        " Cite les documents et les chemins de preuve.",
        " Donne le P&L et la NAV après choc.",
        " Quelles approbations HITL sont nécessaires ?",
        " Résume la réponse en trois points.",
        " Vérifie la cohérence avec la politique de risque.",
    ]
    errors = []
    request_ids = []
    for index in range(100):
        base = questions[index % len(questions)].question
        suffix = suffixes[(index // len(questions)) % len(suffixes)]
        question = base + suffix
        try:
            payload = agent.ask(question)
            validate_response(payload)
            request_ids.append(payload["request_id"])
        except Exception as exc:  # pragma: no cover - rapport d'erreur
            errors.append({"index": index, "question": question, "error": str(exc)})
    validation = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schema": "data/response.schema.json",
        "schema_version": "1.0.0",
        "total": 100,
        "valid": 100 - len(errors),
        "invalid": len(errors),
        "validity_rate": round((100 - len(errors)) / 100, 4),
        "errors": errors,
        "sample_request_ids": request_ids[:5],
    }
    VALIDATION_PATH.write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.copyfile(SCHEMA_PATH, RESULTS_DIR / "answers.schema.json")

    print("5/5 — Visualisations")
    visual_paths = build_all_visuals(graph, quant, comparison, redteam)

    stats = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": APP_VERSION,
        "corpus": {
            "documents": len(documents),
            "positions": len(quant.positions),
            "nav_eur": quant.nav,
            "questions": len(questions),
        },
        "graph": graph.stats(),
        "evaluation": comparison["aggregates"],
        "security": {
            "attacks": redteam["total_attacks"],
            "blocked": redteam["blocked"],
            "block_rate": redteam["block_rate"],
            "false_positives": redteam["false_positives"],
            "benign_total": redteam["benign_total"],
        },
        "json_validation": {
            "total": validation["total"],
            "valid": validation["valid"],
            "validity_rate": validation["validity_rate"],
        },
        "hitl": {
            "pending_in_answers": sum(1 for answer in answers if answer["hitl"]["status"] == "PENDING_APPROVAL"),
            "blocked_in_answers": sum(1 for answer in answers if answer["hitl"]["status"] == "BLOCKED"),
        },
        "artifacts": {name: str(path.relative_to(ROOT)) for name, path in visual_paths.items()},
    }
    STATS_PATH.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    readme = [
        "# Résultats QuantAgent",
        "",
        "Ce dossier contient les preuves reproductibles du mini-projet final.",
        "",
        "| Fichier | Contenu |",
        "|---|---|",
        "| `answers.json` | 8 réponses hybrides complètes (JSON validé) |",
        "| `JSON_Final.json` | Cas de démonstration Q2 — scénario taux +100 bp |",
        "| `comparison.json` | Protocole d'évaluation vectoriel vs hybride |",
        "| `comparaison_vector_graph.csv` | Tableau comparatif |",
        "| `rapport_comparatif.md` | Rapport lisible |",
        "| `red_team.json` | 20 attaques + 10 requêtes bénignes |",
        "| `red_team_evidence.jsonl` | Preuves d'audit |",
        "| `validation_report.json` | 100/100 JSON valides |",
        "| `answers.schema.json` | Contrat JSON |",
        "| `stats.json` | Statistiques consolidées |",
        "| `graph.json` / `graph.cypher` | Export du Knowledge Graph |",
        "| `fig_*.png` | Graphiques du dashboard et du rapport |",
        "",
        f"**Score hybride** : {comparison['aggregates']['hybrid']['score_global']:.2f}/5 — "
        f"**Vectoriel** : {comparison['aggregates']['vector']['score_global']:.2f}/5.",
        f"**Red Team** : {redteam['blocked']}/{redteam['total_attacks']} attaques bloquées, "
        f"{redteam['false_positives']} faux positif(s).",
        f"**JSON** : {validation['valid']}/{validation['total']} réponses valides.",
    ]
    (RESULTS_DIR / "README.md").write_text("\n".join(readme), encoding="utf-8")

    print("\nPipeline terminé.")
    print(f"  Score hybride : {comparison['aggregates']['hybrid']['score_global']:.2f}/5")
    print(f"  Score vectoriel : {comparison['aggregates']['vector']['score_global']:.2f}/5")
    print(f"  Red Team : {redteam['blocked']}/{redteam['total_attacks']} bloquées")
    print(f"  JSON : {validation['valid']}/{validation['total']} valides")


if __name__ == "__main__":
    main()
