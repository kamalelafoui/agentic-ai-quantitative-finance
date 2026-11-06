"""Génération du logo, des architectures et des graphiques."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Circle
from PIL import Image, ImageDraw, ImageFont

from .config import (
    ASSETS_DIR,
    BLUE,
    CORAL,
    DOCS_DIR,
    GOLD,
    LIGHT,
    NAVY,
    NAVY_2,
    RESULTS_DIR,
    SLATE,
    TEAL,
    WHITE,
)

FONT_REG = "C:/Windows/Fonts/segoeui.ttf"
FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_SEMI = "C:/Windows/Fonts/seguisb.ttf"
FONT_LIGHT = "C:/Windows/Fonts/segoeuil.ttf"

TYPE_COLORS = {
    "Portefeuille": NAVY,
    "Position": BLUE,
    "Émetteur": "#7C3AED",
    "Secteur": "#0F766E",
    "Facteur": CORAL,
    "Scénario": GOLD,
    "Politique": "#B45309",
    "Contrôle": "#DC2626",
    "Approbation": "#059669",
    "Réglementation": "#475569",
    "Risque": "#BE123C",
    "Métrique": "#0891B2",
    "Document": "#94A3B8",
    "Watchlist": "#EA580C",
    "Comité": "#4338CA",
    "Modèle": "#6D28D9",
}


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT_REG
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _rounded(draw: ImageDraw.ImageDraw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def make_logo(path: Path | None = None, mark_only: bool = False) -> Path:
    path = path or (ASSETS_DIR / ("favicon.png" if mark_only else "logo.png"))
    path.parent.mkdir(parents=True, exist_ok=True)
    if mark_only:
        size = 256
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        _rounded(draw, (8, 8, size - 8, size - 8), 54, NAVY)
        # Q ring
        draw.ellipse((58, 52, 178, 172), outline=GOLD, width=18)
        draw.line((150, 146, 204, 200), fill=GOLD, width=20)
        # graph nodes
        for (x, y, color) in [(66, 66, TEAL), (178, 72, GOLD), (182, 178, CORAL)]:
            draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=color, outline=WHITE, width=3)
        img.save(path)
        return path

    width, height = 760, 240
    img = Image.new("RGBA", (width, height), WHITE)
    draw = ImageDraw.Draw(img)
    # mark
    _rounded(draw, (28, 34, 214, 220), 38, NAVY)
    draw.ellipse((66, 72, 176, 182), outline=GOLD, width=16)
    draw.line((150, 158, 200, 208), fill=GOLD, width=18)
    for (x, y, color) in [(74, 78, TEAL), (174, 82, GOLD), (178, 178, CORAL)]:
        draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=color, outline=WHITE, width=3)
    # text
    draw.text((242, 50), "QuantAgent", font=_font(68, True), fill=NAVY)
    draw.text((246, 132), "HYBRID GRAPHRAG", font=_font(22, True), fill=GOLD)
    draw.text((246, 162), "QUANTITATIVE FINANCE", font=_font(18, False), fill=SLATE)
    draw.line((246, 202, 704, 202), fill="#E2E8F0", width=2)
    draw.text((246, 208), "Agentic AI · Risk · HITL · Security", font=_font(15, False), fill=SLATE)
    img.save(path)
    return path


def _new_ax(width=16, height=9):
    fig, ax = plt.subplots(figsize=(width, height), dpi=160)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")
    fig.patch.set_facecolor(WHITE)
    ax.set_facecolor(WHITE)
    return fig, ax


def _box(ax, x, y, w, h, title, subtitle="", color=NAVY, text_color=WHITE, fs=12, sub_fs=8.5, radius=0.16):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.03,rounding_size={radius}",
        linewidth=1.2, edgecolor=color, facecolor=color, zorder=2,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h * 0.62, title, ha="center", va="center", color=text_color, fontsize=fs, fontweight="bold", zorder=3)
    if subtitle:
        ax.text(x + w / 2, y + h * 0.28, subtitle, ha="center", va="center", color=text_color, fontsize=sub_fs, zorder=3, linespacing=1.25)


def _arrow(ax, start, end, color=SLATE, width=1.8, style="-|>", rad=0.0, ls="-"):
    arrow = FancyArrowPatch(
        start, end, arrowstyle=style, mutation_scale=16, linewidth=width,
        color=color, connectionstyle=f"arc3,rad={rad}", linestyle=ls, zorder=1,
    )
    ax.add_patch(arrow)


def architecture_global(path: Path | None = None) -> Path:
    path = path or (DOCS_DIR / "architecture_globale.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = _new_ax(16, 9)
    ax.text(0.4, 8.55, "Architecture globale — QuantAgent", fontsize=22, fontweight="bold", color=NAVY)
    ax.text(0.4, 8.18, "Agent hybride : vectoriel + Knowledge Graph + quantification + HITL + sécurité", fontsize=10.5, color=SLATE)

    # top row
    _box(ax, 0.5, 6.7, 2.5, 1.0, "Utilisateurs", "Dashboard · API · CLI", NAVY_2)
    _box(ax, 3.45, 6.7, 2.6, 1.0, "Orchestrateur", "routage d'intention", NAVY)
    _box(ax, 6.5, 6.7, 2.5, 1.0, "Security Gate", "injection · PII · outils", CORAL)
    _box(ax, 9.45, 6.7, 2.7, 1.0, "Contrat JSON", "schéma + validation", TEAL)
    _box(ax, 12.6, 6.7, 2.9, 1.0, "Audit & evidence", "JSONL · traçabilité", SLATE)

    # middle row
    _box(ax, 0.5, 4.35, 2.5, 1.35, "RAG vectoriel", "TF-IDF · top-k · citations", BLUE)
    _box(ax, 3.45, 4.35, 2.6, 1.35, "Knowledge Graph", "105 nœuds · 362 relations", "#7C3AED")
    _box(ax, 6.5, 4.35, 2.5, 1.35, "Moteur quantitatif", "taux · crédit · limites", GOLD, NAVY)
    _box(ax, 9.45, 4.35, 2.7, 1.35, "Politique HITL", "Risk · IC · Compliance", "#059669")
    _box(ax, 12.6, 4.35, 2.9, 1.35, "Policies & contrôles", "6 contrôles · 8 politiques", "#B45309")

    # bottom row
    _box(ax, 0.5, 1.55, 3.4, 1.05, "Données", "22 documents · 12 positions", NAVY_2)
    _box(ax, 4.35, 1.55, 3.1, 1.05, "Scénarios", "+100 bp · crédit · actions", CORAL)
    _box(ax, 7.9, 1.55, 3.0, 1.05, "Décision humaine", "APPROUVER · REJETER · ESCALADER", "#059669")
    _box(ax, 11.35, 1.55, 4.15, 1.05, "Industrialisation", "Docker · n8n · GitHub Actions · tests", SLATE)

    # arrows
    _arrow(ax, (3.0, 7.2), (3.45, 7.2))
    _arrow(ax, (6.05, 7.2), (6.5, 7.2), color=CORAL)
    _arrow(ax, (9.0, 7.2), (9.45, 7.2), color=TEAL)
    _arrow(ax, (12.15, 7.2), (12.6, 7.2), color=SLATE)
    _arrow(ax, (4.75, 6.7), (4.75, 5.7), color=BLUE)
    _arrow(ax, (4.75, 5.7), (3.0, 5.05), color=BLUE, rad=0.05)
    _arrow(ax, (4.75, 5.7), (6.5, 5.05), color="#7C3AED", rad=-0.05)
    _arrow(ax, (4.75, 5.7), (7.75, 5.05), color=GOLD, rad=-0.1)
    _arrow(ax, (9.0, 5.05), (9.45, 5.05), color="#059669")
    _arrow(ax, (12.15, 5.05), (12.6, 5.05), color="#B45309")
    _arrow(ax, (10.8, 4.35), (10.8, 2.6), color="#059669")
    _arrow(ax, (6.5, 4.35), (5.9, 2.6), color=CORAL, rad=0.1)
    _arrow(ax, (2.4, 4.35), (2.2, 2.6), color=NAVY_2, rad=-0.1)
    _arrow(ax, (13.2, 4.35), (13.4, 2.6), color=SLATE, rad=0.1)
    _arrow(ax, (12.0, 2.07), (11.35, 2.07), color="#059669", style="-|>")
    ax.text(8.0, 0.65, "Chaque sortie est un JSON validé, cité, chiffré et soumis à HITL si nécessaire.", ha="center", fontsize=9.5, color=SLATE, style="italic")
    fig.savefig(path, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    return path


def architecture_agent(path: Path | None = None) -> Path:
    path = path or (DOCS_DIR / "architecture_agent.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = _new_ax(16, 9)
    ax.text(0.4, 8.55, "Boucle de l'agent — 9 étapes", fontsize=22, fontweight="bold", color=NAVY)
    ax.text(0.4, 8.18, "Comprendre → router → récupérer → étendre → quantifier → contrôler → valider → répondre → auditer", fontsize=10.5, color=SLATE)
    steps = [
        ("1. Comprendre", "question + entités", NAVY_2),
        ("2. Router", "intention métier", NAVY),
        ("3. RAG vectoriel", "passages TF-IDF", BLUE),
        ("4. Graphe", "expansion multi-hop", "#7C3AED"),
        ("5. Quantifier", "P&L · limites", GOLD),
        ("6. Policies", "HITL · sécurité", "#059669"),
        ("7. Composer", "réponse citée", TEAL),
        ("8. Valider JSON", "schéma 100 %", SLATE),
        ("9. Auditer", "trace + evidence", CORAL),
    ]
    # Disposition en serpentin : 3 lignes de 3 étapes.
    positions = {
        0: (0.8, 6.45), 1: (6.0, 6.45), 2: (11.2, 6.45),
        5: (0.8, 4.05), 4: (6.0, 4.05), 3: (11.2, 4.05),
        6: (0.8, 1.65), 7: (6.0, 1.65), 8: (11.2, 1.65),
    }
    for index, (title, subtitle, color) in enumerate(steps):
        x, y = positions[index]
        _box(ax, x, y, 4.0, 1.15, title, subtitle, color, fs=12, sub_fs=8.5)
    # Flèches du serpentin
    _arrow(ax, (4.8, 7.02), (6.0, 7.02), color=SLATE)
    _arrow(ax, (10.0, 7.02), (11.2, 7.02), color=SLATE)
    _arrow(ax, (13.2, 6.45), (13.2, 5.20), color=SLATE)
    _arrow(ax, (11.2, 4.62), (10.0, 4.62), color=SLATE)
    _arrow(ax, (6.0, 4.62), (4.8, 4.62), color=SLATE)
    _arrow(ax, (2.8, 4.05), (2.8, 2.80), color=SLATE)
    _arrow(ax, (4.8, 2.22), (6.0, 2.22), color=SLATE)
    _arrow(ax, (10.0, 2.22), (11.2, 2.22), color=SLATE)
    ax.text(8.0, 0.65, "Le agent ne prend jamais de décision d'exécution : il prépare un dossier et attend la validation humaine.", ha="center", fontsize=9.5, color=SLATE, style="italic")
    fig.savefig(path, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    return path


def workflow_hitl(path: Path | None = None) -> Path:
    path = path or (DOCS_DIR / "workflow_hitl.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = _new_ax(16, 6.5)
    ax.text(0.4, 6.1, "Workflow HITL — de la proposition à la décision", fontsize=22, fontweight="bold", color=NAVY)
    ax.text(0.4, 5.75, "Le agent prépare ; l'humain décide ; le système journalise.", fontsize=10.5, color=SLATE)
    y = 3.1
    _box(ax, 0.4, y, 2.3, 1.0, "Agent", "proposition chiffrée", NAVY)
    _box(ax, 3.0, y, 2.4, 1.0, "Risk", "4 h · limites", CORAL)
    _box(ax, 5.7, y, 2.4, 1.0, "Comité IC", "24 h · > 2,5 % NAV", GOLD, NAVY)
    _box(ax, 8.4, y, 2.4, 1.0, "Compliance", "24 h · ESG / PII", "#B45309")
    _box(ax, 11.1, y, 2.0, 1.0, "Décision", "humaine", "#059669")
    _box(ax, 13.4, y, 2.2, 1.0, "Exécution", "simulée / journalisée", SLATE)
    for x in [2.7, 5.4, 8.1, 10.8, 13.1]:
        _arrow(ax, (x, y + 0.5), (x + 0.3, y + 0.5), color=SLATE)
    _arrow(ax, (12.1, y), (12.1, 1.75), color=CORAL, style="-|>")
    _box(ax, 10.5, 1.05, 3.2, 0.7, "REJETER / ESCALADER", "retour Risk + audit", CORAL, fs=9.5, sub_fs=7.5)
    ax.text(8.0, 0.45, "Aucune opération n'est exécutée automatiquement. Chaque décision est horodatée et conservée 5 ans.", ha="center", fontsize=9.5, color=SLATE, style="italic")
    fig.savefig(path, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    return path


def security_layers(path: Path | None = None) -> Path:
    path = path or (DOCS_DIR / "security_layers.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = _new_ax(16, 7.5)
    ax.text(0.4, 7.05, "Défense en profondeur — 5 couches", fontsize=22, fontweight="bold", color=NAVY)
    ax.text(0.4, 6.68, "Chaque couche peut bloquer, masquer ou journaliser.", fontsize=10.5, color=SLATE)
    layers = [
        ("1. Entrée", "injection · jailbreak · PII", CORAL),
        ("2. Retrieval", "documents piégés isolés", "#B45309"),
        ("3. Outils", "allowlist · pas de shell", GOLD),
        ("4. Sortie", "masquage PII · refus", TEAL),
        ("5. Audit", "evidence JSONL · revue", NAVY),
    ]
    for index, (title, subtitle, color) in enumerate(layers):
        x = 0.6 + index * 3.0
        _box(ax, x, 3.4, 2.55, 1.4, title, subtitle, color, fs=12, sub_fs=8)
        if index < len(layers) - 1:
            _arrow(ax, (x + 2.55, 4.1), (x + 3.0, 4.1), color=SLATE)
    ax.text(8.0, 2.55, "20 attaques Red Team · 100 % bloquées · 0 faux positif sur 10 requêtes bénignes", ha="center", fontsize=11, color=NAVY, fontweight="bold")
    ax.text(8.0, 0.55, "Le prompt système, les positions confidentielles et les données client ne sortent jamais.", ha="center", fontsize=9.5, color=SLATE, style="italic")
    fig.savefig(path, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    return path


def graph_overview(graph, path: Path | None = None) -> Path:
    path = path or (DOCS_DIR / "graph_overview.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    degrees = dict(graph.graph.degree())
    keep = set(graph.find_entities("portefeuille Core Europe scénario taux politique HITL ESG Vonovia EDF Enel BNP AXA Bund", max_entities=32))
    keep.update([node for node, degree in sorted(degrees.items(), key=lambda item: item[1], reverse=True)[:36]])
    sub = graph.graph.subgraph(keep).copy()
    pos = nx.kamada_kawai_layout(sub)
    fig, ax = plt.subplots(figsize=(17, 10.5), dpi=150)
    fig.patch.set_facecolor(WHITE)
    ax.set_facecolor(WHITE)
    for u, v in sub.edges():
        ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], color="#D7DEE8", linewidth=0.45, alpha=0.7, zorder=1)
    for ntype, color in TYPE_COLORS.items():
        nodes = [node for node in sub.nodes if graph.type_of(node) == ntype]
        if not nodes:
            continue
        sizes = [60 + 15 * min(degrees.get(node, 1), 16) for node in nodes]
        ax.scatter([pos[node][0] for node in nodes], [pos[node][1] for node in nodes], s=sizes, c=color, edgecolors=WHITE, linewidths=0.9, label=ntype, zorder=2, alpha=0.95)
    top_labels = sorted(sub.nodes, key=lambda node: degrees.get(node, 1), reverse=True)[:14]
    for node in top_labels:
        label = graph.label(node)
        if len(label) > 34:
            label = label[:31] + "…"
        ax.annotate(
            label, pos[node], xytext=(4, 4), textcoords="offset points",
            fontsize=6.8, color=NAVY, zorder=3,
            bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.82),
        )
    ax.legend(loc="lower left", ncol=5, fontsize=7.2, frameon=True, framealpha=0.95, edgecolor="#E2E8F0")
    ax.set_title("Graphe de connaissances QuantAgent — vue simplifiée", fontsize=18, fontweight="bold", color=NAVY, loc="left", pad=14)
    ax.axis("off")
    ax.margins(0.08)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    return path


def chart_sector_allocation(quant, path: Path | None = None) -> Path:
    path = path or (RESULTS_DIR / "fig_sector_allocation.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = quant.sector_allocation()
    names = {
        "SEC-BANKS": "Banques", "SEC-ENERGY": "Énergie", "SEC-REALESTATE": "Immobilier",
        "SEC-UTILITIES": "Utilities", "SEC-TECH": "Technologie", "SEC-MATERIALS": "Matériaux",
        "SEC-TELECOM": "Télécom", "SEC-INSURANCE": "Assurance", "SEC-SOVEREIGN": "Souverain",
        "SEC-CASH": "Cash",
    }
    labels = [names.get(row["sector_id"], row["sector_id"]) for row in rows]
    values = [row["weight_pct"] for row in rows]
    colors = [NAVY, BLUE, TEAL, GOLD, CORAL, "#7C3AED", "#0F766E", "#B45309", "#64748B", "#94A3B8"]
    fig, ax = plt.subplots(figsize=(9.5, 5.0), dpi=160)
    fig.patch.set_facecolor(WHITE)
    bars = ax.barh(labels, values, color=colors[:len(values)], height=0.62)
    for bar, value in zip(bars, values):
        ax.text(value + 0.25, bar.get_y() + bar.get_height() / 2, f"{value:.1f}%".replace(".", ","), va="center", fontsize=8.5, color=NAVY, fontweight="bold")
    ax.invert_yaxis()
    ax.set_xlim(0, max(values) + 3.5)
    ax.set_xlabel("Poids (% NAV)", fontsize=9, color=SLATE)
    ax.set_title("Allocation sectorielle — Core Europe (250 M€)", fontsize=14, fontweight="bold", color=NAVY, loc="left")
    ax.grid(axis="x", color="#EDF1F6", linewidth=0.8)
    ax.tick_params(colors=SLATE, labelsize=8.5)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    return path


def chart_scenario_impact(quant, path: Path | None = None) -> Path:
    path = path or (RESULTS_DIR / "fig_scenario_impact.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = quant["top_contributors"][:7]
    names = [row["name"] for row in rows][::-1]
    values = [row["impact_eur"] / 1e6 for row in rows][::-1]
    colors = [CORAL if value < 0 else TEAL for value in values]
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=160)
    fig.patch.set_facecolor(WHITE)
    bars = ax.barh(names, values, color=colors, height=0.62)
    for bar, value in zip(bars, values):
        ax.text(value / 2, bar.get_y() + bar.get_height() / 2, f"{value:+.2f} M€".replace(".", ","), va="center", ha="center", fontsize=8.5, color=WHITE, fontweight="bold")
    ax.axvline(0, color=SLATE, linewidth=0.8)
    ax.set_xlabel("Impact P&L (M€) — choc +100 bp", fontsize=9, color=SLATE)
    ax.set_title("Top contributeurs au scénario de taux", fontsize=14, fontweight="bold", color=NAVY, loc="left")
    ax.grid(axis="x", color="#EDF1F6", linewidth=0.8)
    ax.tick_params(colors=SLATE, labelsize=8.5)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    return path


def chart_limit_utilization(quant, path: Path | None = None) -> Path:
    path = path or (RESULTS_DIR / "fig_limit_utilization.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    checks = quant["limit_checks"]
    labels = [check["name"] for check in checks]
    ratios = []
    colors = []
    for check in checks:
        if check["control"] == "CTL-LIQUIDITY":
            ratio = check["limit"] / max(check["value"], 1e-9) * 100
        else:
            ratio = check["value"] / check["limit"] * 100
        ratios.append(ratio)
        colors.append(CORAL if check["status"] == "BREACH" else (GOLD if check["status"] == "WATCH" else TEAL))
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=160)
    fig.patch.set_facecolor(WHITE)
    bars = ax.barh(labels[::-1], ratios[::-1], color=colors[::-1], height=0.58)
    ax.axvline(100, color=CORAL, linestyle="--", linewidth=1.2, label="Limite")
    for bar, ratio, check in zip(bars, ratios[::-1], checks[::-1]):
        ax.text(ratio + 1.5, bar.get_y() + bar.get_height() / 2, f"{ratio:.0f}%", va="center", fontsize=8, color=NAVY, fontweight="bold")
    ax.set_xlim(0, max(135, max(ratios) + 20))
    ax.set_xlabel("Utilisation de la limite (%)", fontsize=9, color=SLATE)
    ax.set_title("Utilisation des limites — scénario +100 bp", fontsize=14, fontweight="bold", color=NAVY, loc="left")
    ax.grid(axis="x", color="#EDF1F6", linewidth=0.8)
    ax.tick_params(colors=SLATE, labelsize=8.5)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    return path


def chart_comparison(report, path: Path | None = None) -> Path:
    path = path or (RESULTS_DIR / "fig_comparison.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    metrics = ["pertinence", "exactitude", "tracabilite", "multi_hop", "score_global"]
    labels = ["Pertinence", "Exactitude", "Traçabilité", "Multi-hop", "Score global"]
    vector = [report["aggregates"]["vector"][metric] for metric in metrics]
    hybrid = [report["aggregates"]["hybrid"][metric] for metric in metrics]
    x = np.arange(len(metrics))
    width = 0.36
    fig, ax = plt.subplots(figsize=(9.5, 4.8), dpi=160)
    fig.patch.set_facecolor(WHITE)
    ax.bar(x - width / 2, vector, width, label="Vectoriel TF-IDF", color="#94A3B8")
    ax.bar(x + width / 2, hybrid, width, label="QuantAgent hybride", color=GOLD)
    for index, (v, h) in enumerate(zip(vector, hybrid)):
        ax.text(index - width / 2, v + 0.08, f"{v:.2f}", ha="center", fontsize=7.5, color=SLATE)
        ax.text(index + width / 2, h + 0.08, f"{h:.2f}", ha="center", fontsize=7.5, color=NAVY, fontweight="bold")
    ax.set_xticks(x, labels, fontsize=8.5, color=SLATE)
    ax.set_ylim(0, 5.6)
    ax.set_ylabel("Score / 5", fontsize=9, color=SLATE)
    ax.set_title("Évaluation — vectoriel vs agent hybride", fontsize=14, fontweight="bold", color=NAVY, loc="left")
    ax.grid(axis="y", color="#EDF1F6", linewidth=0.8)
    ax.legend(fontsize=8, frameon=False, loc="lower right", bbox_to_anchor=(1.0, 1.01), ncol=2)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    return path


def chart_redteam(report, path: Path | None = None) -> Path:
    path = path or (RESULTS_DIR / "fig_redteam.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    categories = report["categories"]
    labels = list(categories.keys())
    blocked = [categories[key]["blocked"] for key in labels]
    total = [categories[key]["total"] for key in labels]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(9.5, 4.4), dpi=160)
    fig.patch.set_facecolor(WHITE)
    ax.bar(x, total, width=0.55, color="#E2E8F0", label="Total")
    ax.bar(x, blocked, width=0.55, color=CORAL, label="Bloquées")
    for index, (b, t) in enumerate(zip(blocked, total)):
        ax.text(index, t + 0.1, f"{b}/{t}", ha="center", fontsize=8, color=NAVY, fontweight="bold")
    ax.set_xticks(x, [label.replace("_", "\n") for label in labels], fontsize=8, color=SLATE)
    ax.set_ylim(0, max(total) + 1.5)
    ax.set_ylabel("Attaques", fontsize=9, color=SLATE)
    ax.set_title("Red Team — taux de blocage par catégorie", fontsize=14, fontweight="bold", color=NAVY, loc="left")
    ax.grid(axis="y", color="#EDF1F6", linewidth=0.8)
    ax.legend(fontsize=8, frameon=False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    return path


def build_all_visuals(graph, quant, report, redteam_report) -> dict[str, Path]:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "logo": make_logo(),
        "favicon": make_logo(mark_only=True),
        "architecture_global": architecture_global(),
        "architecture_agent": architecture_agent(),
        "workflow_hitl": workflow_hitl(),
        "security_layers": security_layers(),
        "graph_overview": graph_overview(graph),
        "sector_allocation": chart_sector_allocation(quant),
        "scenario_impact": chart_scenario_impact(quant.run_scenario("SCN-RATES-100BP")),
        "limit_utilization": chart_limit_utilization(quant.run_scenario("SCN-RATES-100BP")),
        "comparison": chart_comparison(report),
        "redteam": chart_redteam(redteam_report),
    }
    return paths



