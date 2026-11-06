#!/usr/bin/env python3
"""QuantAgent — CLI du mini-projet final Agentic AI for Quantitative Finance."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from quantagent.agent import QuantAgent
from quantagent.config import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_PORT,
    RESULTS_DIR,
    STATS_PATH,
    VALIDATION_PATH,
)
from quantagent.corpus import load_corpus, load_questions
from quantagent.evaluation import run_comparison
from quantagent.knowledge_graph import KnowledgeGraph
from quantagent.quant import QuantEngine
from quantagent.redteam import run_campaign

ROOT = Path(__file__).resolve().parent


def banner():
    print(f"\n{APP_NAME} v{APP_VERSION} — Agentic AI for Quantitative Finance")
    print("Agent hybride · GraphRAG · Quant · HITL · Security\n")


def build_agent() -> QuantAgent:
    return QuantAgent(load_corpus(), KnowledgeGraph.from_files(), quant=QuantEngine())


def cmd_build(args):
    for script in ["build_data.py", "build_graph.py"]:
        subprocess.run([sys.executable, str(ROOT / "scripts" / script)], check=True)
    graph = KnowledgeGraph.from_files()
    graph.save_json()
    graph.save_cypher()
    print(f"Graphe : {graph.stats()['nodes']} nœuds, {graph.stats()['edges']} relations")


def cmd_ask(args):
    agent = build_agent()
    result = agent.ask(args.question, scenario_id=args.scenario, mode=args.mode)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(f"Question : {args.question}\n")
    print(result["answer"])
    print(f"\nConfiance : {result['confidence']*100:.0f} % · Latence : {result['latency_ms']:.0f} ms")
    print(f"Intent : {result['intent']} · HITL : {result['hitl']['status']} · JSON : {result['meta']['json_valid']}")
    print(f"Sources : {', '.join(source['doc_id'] for source in result['sources'])}")
    if result["graph"]["paths"]:
        print(f"Chemins de preuve : {len(result['graph']['paths'])}")


def cmd_compare(args):
    agent = build_agent()
    questions = load_questions()
    report = run_comparison(agent, questions, agent.graph)
    print("Résultats globaux (0-5) :\n")
    print(f"{'Métrique':<16}{'Vectoriel':>12}{'Hybride':>12}")
    for metric in ["pertinence", "exactitude", "tracabilite", "multi_hop", "score_global"]:
        print(f"{metric:<16}{report['aggregates']['vector'][metric]:>12.2f}{report['aggregates']['hybrid'][metric]:>12.2f}")
    print(f"\nHybride gagne {report['aggregates']['graph_wins']}/{len(questions)} questions "
          f"({report['aggregates']['hybrid']['score_global']:.2f} vs {report['aggregates']['vector']['score_global']:.2f}).")


def cmd_demo(args):
    subprocess.run([sys.executable, str(ROOT / "scripts" / "run_pipeline.py")], check=True)


def cmd_stats(args):
    if STATS_PATH.exists():
        print(STATS_PATH.read_text(encoding="utf-8"))
    else:
        graph = KnowledgeGraph.from_files()
        print(json.dumps(graph.stats(), ensure_ascii=False, indent=2))


def cmd_serve(args):
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py"),
        "--server.port", str(args.port), "--server.address", args.address,
        "--server.headless", "true", "--browser.gatherUsageStats", "false",
    ], check=False)


def cmd_api(args):
    subprocess.run([
        sys.executable, "-m", "uvicorn", "api:app", "--host", args.host, "--port", str(args.port),
    ], cwd=ROOT, check=False)


def cmd_redteam(args):
    report = run_campaign(build_agent())
    print(f"Red Team : {report['blocked']}/{report['total_attacks']} attaques bloquées · "
          f"{report['false_positives']} faux positif(s) · taux {report['block_rate']*100:.0f} %")


def cmd_validate(args):
    if args.run:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "run_pipeline.py")], check=True)
    if VALIDATION_PATH.exists():
        report = json.loads(VALIDATION_PATH.read_text(encoding="utf-8"))
        print(f"JSON : {report['valid']}/{report['total']} valides ({report['validity_rate']*100:.0f} %)")
        if report["errors"]:
            print(json.dumps(report["errors"], ensure_ascii=False, indent=2))
    else:
        print("Aucun rapport de validation. Lancez `python main.py validate --run`.")


def cmd_export(args):
    graph = KnowledgeGraph.from_files()
    print(graph.save_json())
    print(graph.save_cypher())


def build_parser():
    parser = argparse.ArgumentParser(description=f"{APP_NAME} — mini-projet final")
    parser.add_argument("--version", action="version", version=APP_VERSION)
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Régénérer les données et le graphe")
    build.set_defaults(func=cmd_build)

    ask = sub.add_parser("ask", help="Poser une question à l'agent")
    ask.add_argument("question")
    ask.add_argument("--mode", choices=["hybrid", "vector", "graph"], default="hybrid")
    ask.add_argument("--scenario", default=None)
    ask.add_argument("--json", action="store_true")
    ask.set_defaults(func=cmd_ask)

    compare = sub.add_parser("compare", help="Comparer vectoriel et hybride")
    compare.set_defaults(func=cmd_compare)

    demo = sub.add_parser("demo", help="Pipeline complet (évaluation + Red Team + JSON + visuels)")
    demo.set_defaults(func=cmd_demo)

    stats = sub.add_parser("stats", help="Afficher les statistiques")
    stats.set_defaults(func=cmd_stats)

    serve = sub.add_parser("serve", help="Lancer le dashboard Streamlit")
    serve.add_argument("--port", type=int, default=DEFAULT_PORT)
    serve.add_argument("--address", default="127.0.0.1")
    serve.set_defaults(func=cmd_serve)

    api = sub.add_parser("api", help="Lancer l'API FastAPI")
    api.add_argument("--port", type=int, default=8000)
    api.add_argument("--host", default="127.0.0.1")
    api.set_defaults(func=cmd_api)

    redteam = sub.add_parser("redteam", help="Lancer la campagne Red Team")
    redteam.set_defaults(func=cmd_redteam)

    validate = sub.add_parser("validate", help="Vérifier le rapport JSON 100/100")
    validate.add_argument("--run", action="store_true")
    validate.set_defaults(func=cmd_validate)

    export = sub.add_parser("export", help="Exporter le graphe JSON + Cypher")
    export.set_defaults(func=cmd_export)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command in {"ask", "compare", "redteam"}:
        banner()
    args.func(args)


if __name__ == "__main__":
    main()
