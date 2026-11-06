"""Configuration centrale de QuantAgent."""

from __future__ import annotations

from pathlib import Path

APP_NAME = "QuantAgent"
APP_TAGLINE = "Agent hybride GraphRAG pour la finance quantitative"
APP_VERSION = "1.0.0"
AUTHOR = "KAMAL EL AFOUI"
PROGRAM = "Agentic AI for Quantitative Finance — Mini-projet final"
DATE = "Novembre 2026"
PORTFOLIO_ID = "PF-CORE-EU"
DEFAULT_PORT = 8007

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
DOCS_DIR = ROOT / "docs"
ASSETS_DIR = ROOT / "assets"
WORKFLOWS_DIR = ROOT / "workflows"
NOTEBOOKS_DIR = ROOT / "notebooks"

CORPUS_PATH = DATA_DIR / "corpus.json"
NODES_PATH = DATA_DIR / "nodes.json"
EDGES_PATH = DATA_DIR / "edges.json"
QUESTIONS_PATH = DATA_DIR / "questions.json"
PORTFOLIO_PATH = DATA_DIR / "portfolio.json"
SCENARIOS_PATH = DATA_DIR / "scenarios.json"
SCHEMA_PATH = DATA_DIR / "response.schema.json"
STATS_PATH = RESULTS_DIR / "stats.json"
GRAPH_PATH = RESULTS_DIR / "graph.json"
ANSWERS_PATH = RESULTS_DIR / "answers.json"
COMPARISON_PATH = RESULTS_DIR / "comparison.json"
REDTEAM_PATH = RESULTS_DIR / "red_team.json"
EVIDENCE_PATH = RESULTS_DIR / "red_team_evidence.jsonl"
VALIDATION_PATH = RESULTS_DIR / "validation_report.json"
HITL_LOG_PATH = RESULTS_DIR / "hitl_decisions.jsonl"

# Palette de la marque
NAVY = "#0B2545"
NAVY_2 = "#123B66"
GOLD = "#F2C230"
TEAL = "#2EC4B6"
CORAL = "#E4572E"
BLUE = "#2D6CDF"
SLATE = "#5B6778"
LIGHT = "#F7F9FC"
WHITE = "#FFFFFF"

DISCLAIMER = (
    "QuantAgent est un outil de recherche et de démonstration. "
    "Ses sorties ne constituent ni un conseil en investissement, ni une recommandation "
    "personnalisée, ni une exécution d'ordre. Toute décision reste soumise à validation humaine."
)
