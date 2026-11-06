"""Construit le notebook reproductible QuantAgent."""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = ROOT / "notebooks"
NOTEBOOKS.mkdir(exist_ok=True)
OUT = NOTEBOOKS / "QuantAgent_Agentic_AI_Quantitative_Finance.ipynb"

nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.12"},
}

cells = []
cells.append(nbf.v4.new_markdown_cell("""# QuantAgent — Agentic AI for Quantitative Finance

**Mini-projet final — agent hybride GraphRAG, quantification, HITL et sécurité.**

Auteur : **KAMAL EL AFOUI** · Novembre 2026

Ce notebook reproduit le pipeline complet :

1. chargement du corpus et du graphe ;
2. scénario de taux +100 bp ;
3. réponse JSON de l'agent ;
4. comparaison vectoriel vs hybride ;
5. campagne Red Team ;
6. validation JSON 100/100 ;
7. dashboard et livrables.

![Logo](../assets/logo.png)
"""))

cells.append(nbf.v4.new_code_cell("""import json
import sys
from pathlib import Path

import pandas as pd
from IPython.display import Image, JSON, Markdown, display

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quantagent.agent import QuantAgent
from quantagent.corpus import load_corpus, load_questions
from quantagent.evaluation import run_comparison
from quantagent.knowledge_graph import KnowledgeGraph
from quantagent.quant import QuantEngine
from quantagent.redteam import run_campaign
from quantagent.schema import validate_response

pd.set_option("display.max_colwidth", 120)
print("Racine :", ROOT)
"""))

cells.append(nbf.v4.new_markdown_cell("""## 1. Corpus et Knowledge Graph

Le corpus contient 22 documents financiers synthétiques. Le graphe relie portefeuille, positions, émetteurs, secteurs, facteurs, scénarios, politiques, contrôles, approbations et documents."""))
cells.append(nbf.v4.new_code_cell("""documents = load_corpus()
graph = KnowledgeGraph.from_files()
quant = QuantEngine()
agent = QuantAgent(documents, graph, quant=quant)
questions = load_questions()
stats = graph.stats()

display(pd.DataFrame([
    {"Indicateur": "Documents", "Valeur": len(documents)},
    {"Indicateur": "Positions", "Valeur": len(quant.positions)},
    {"Indicateur": "NAV (M€)", "Valeur": quant.nav / 1e6},
    {"Indicateur": "Nœuds", "Valeur": stats["nodes"]},
    {"Indicateur": "Relations", "Valeur": stats["edges"]},
    {"Indicateur": "Densité", "Valeur": stats["density"]},
    {"Indicateur": "Questions", "Valeur": len(questions)},
]))
display(pd.DataFrame([{"type": key, "count": value} for key, value in stats["node_types"].items()]))
"""))

cells.append(nbf.v4.new_markdown_cell("""## 2. Scénario de taux +100 bp

Le moteur quantitatif applique la formule `P&L = -MV × duration × Δy` aux obligations et un bêta taux aux actions."""))
cells.append(nbf.v4.new_code_cell("""scenario = quant.run_scenario("SCN-RATES-100BP")
print(f"Impact : {scenario['impact_eur']/1e6:+.2f} M€ ({scenario['impact_pct_nav']:+.2f} % NAV)")
display(pd.DataFrame(scenario["top_contributors"])[["name", "impact_eur", "impact_pct_nav", "driver"]])
display(pd.DataFrame(scenario["limit_checks"]))
display(Image(filename=str(ROOT / "results" / "fig_scenario_impact.png"), width=900))
"""))

cells.append(nbf.v4.new_markdown_cell("""## 3. Réponse JSON de l'agent — Q2

L'agent combine le vectoriel, le graphe, le calcul et la politique HITL. La sortie est validée contre le schéma JSON Draft 2020-12."""))
cells.append(nbf.v4.new_code_cell("""q2 = next(question for question in questions if question.id == "Q2")
result = agent.ask(q2.question)
display(Markdown(result["answer"]))
print("JSON valide :", validate_response(result))
print("Intent :", result["intent"], "| HITL :", result["hitl"]["status"], "| Confiance :", result["confidence"])
print("Sources :", ", ".join(source["doc_id"] for source in result["sources"]))
display(JSON(result))
"""))

cells.append(nbf.v4.new_markdown_cell("""## 4. Comparaison vectoriel vs hybride

Protocole 0-5 sur 8 questions : pertinence, exactitude, traçabilité, multi-hop, score global."""))
cells.append(nbf.v4.new_code_cell("""comparison = run_comparison(agent, questions, graph)
display(pd.DataFrame([
    {"Métrique": metric, "Vectoriel": comparison["aggregates"]["vector"][metric], "Hybride": comparison["aggregates"]["hybrid"][metric]}
    for metric in ["pertinence", "exactitude", "tracabilite", "multi_hop", "score_global"]
]))
display(Image(filename=str(ROOT / "results" / "fig_comparison.png"), width=900))
"""))

cells.append(nbf.v4.new_markdown_cell("""## 5. Red Team — 20 attaques, 0 faux positif

Les documents piégés sont isolés dans `data/attack_pack/` et ne sont jamais indexés."""))
cells.append(nbf.v4.new_code_cell("""redteam = run_campaign(agent)
print(f"Bloquées : {redteam['blocked']}/{redteam['total_attacks']} ({redteam['block_rate']*100:.0f} %)")
print(f"Faux positifs : {redteam['false_positives']}/{redteam['benign_total']}")
display(pd.DataFrame(redteam["attacks"])[["id", "category", "status", "risk_score", "blocked"]])
"""))

cells.append(nbf.v4.new_markdown_cell("""## 6. Validation JSON 100/100

Le rapport de validation est généré par `python main.py validate --run`."""))
cells.append(nbf.v4.new_code_cell("""validation = json.loads((ROOT / "results" / "validation_report.json").read_text(encoding="utf-8"))
print(f"JSON valides : {validation['valid']}/{validation['total']} ({validation['validity_rate']*100:.0f} %)")
print("Erreurs :", len(validation["errors"]))
"""))

cells.append(nbf.v4.new_markdown_cell("""## 7. Dashboard et livrables

Dashboard : `python main.py serve` → http://localhost:8007

Livrables : documentation DOCX/PDF, présentation PPTX, workflow n8n, Docker, GitHub, archive ZIP."""))
cells.append(nbf.v4.new_code_cell("""display(Image(filename=str(ROOT / "docs" / "dashboard_home.png"), width=1000))
display(Image(filename=str(ROOT / "docs" / "architecture_globale.png"), width=1000))
print("Documentation :", (ROOT / "docs" / "Documentation_Agentic_AI_Quantitative_Finance.pdf").exists())
print("Présentation :", (ROOT / "docs" / "Presentation_Agentic_AI_Quantitative_Finance.pptx").exists())
"""))

nb.cells = cells
nbf.write(nb, OUT)
print(OUT)
