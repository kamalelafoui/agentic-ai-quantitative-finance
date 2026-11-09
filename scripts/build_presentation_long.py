"""Génère la présentation PPTX de QuantAgent."""

from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
RESULTS = ROOT / "results"

NAVY = RGBColor(0x0B, 0x25, 0x45)
NAVY_2 = RGBColor(0x12, 0x3B, 0x66)
GOLD = RGBColor(0xF2, 0xC2, 0x30)
TEAL = RGBColor(0x2E, 0xC4, 0xB6)
CORAL = RGBColor(0xE4, 0x57, 0x2E)
BLUE = RGBColor(0x2D, 0x6C, 0xDF)
SLATE = RGBColor(0x5B, 0x67, 0x78)
LIGHT = RGBColor(0xF4, 0xF7, 0xFB)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
PALE = RGBColor(0xE8, 0xF0, 0xFA)

STATS = json.loads((RESULTS / "stats.json").read_text(encoding="utf-8"))
COMPARISON = json.loads((RESULTS / "comparison.json").read_text(encoding="utf-8"))
REDTEAM = json.loads((RESULTS / "red_team.json").read_text(encoding="utf-8"))
VALIDATION = json.loads((RESULTS / "validation_report.json").read_text(encoding="utf-8"))
SHOWCASE = json.loads((RESULTS / "JSON_Final.json").read_text(encoding="utf-8"))

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW = 13.333
SH = 7.5


def add_slide(bg=WHITE):
    slide = prs.slides.add_slide(BLANK)
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = bg
    return slide


def _rgb(color):
    if isinstance(color, str):
        return RGBColor.from_string(color.replace('#', ''))
    return color


def box(slide, x, y, w, h, fill, line=None, radius=True, line_width=1.0):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(fill)
    if line:
        shape.line.color.rgb = _rgb(line)
        shape.line.width = Pt(line_width)
    else:
        shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def text(slide, x, y, w, h, content, size=16, color=NAVY, bold=False, align=PP_ALIGN.LEFT, font="Segoe UI", anchor=MSO_ANCHOR.TOP, italic=False):
    textbox = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = textbox.text_frame
    frame.word_wrap = True
    frame.vertical_anchor = anchor
    frame.margin_left = 0
    frame.margin_right = 0
    frame.margin_top = 0
    frame.margin_bottom = 0
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    run = paragraph.add_run()
    run.text = content
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = _rgb(color)
    run.font.name = font
    return textbox


def bullets(slide, x, y, w, h, items, size=13, color=SLATE, spacing=8):
    textbox = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = textbox.text_frame
    frame.word_wrap = True
    frame.margin_left = 0
    frame.margin_right = 0
    for index, item in enumerate(items):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.space_after = Pt(spacing)
        paragraph.level = 0
        run = paragraph.add_run()
        run.text = "•  " + item
        run.font.size = Pt(size)
        run.font.color.rgb = _rgb(color)
        run.font.name = "Segoe UI"
    return textbox


def title(slide, heading, subtitle=None, dark=False):
    color = WHITE if dark else NAVY
    text(slide, 0.65, 0.38, 11.8, 0.7, heading, size=28, color=color, bold=True)
    if subtitle:
        text(slide, 0.68, 1.05, 11.8, 0.4, subtitle, size=12.5, color=PALE if dark else SLATE)
    # gold accent
    box(slide, 0.65, 1.48, 0.75, 0.07, GOLD, radius=False)


def footer(slide, page=None, dark=False):
    page = len(prs.slides) if page is None else page
    color = PALE if dark else SLATE
    text(slide, 0.65, 7.12, 5.5, 0.25, "QuantAgent  ·  Agentic AI for Quantitative Finance", size=8.5, color=color)
    text(slide, 11.4, 7.12, 1.3, 0.25, f"{page:02d}", size=8.5, color=color, align=PP_ALIGN.RIGHT)
    if (ROOT / "assets" / "logo.png").exists():
        slide.shapes.add_picture(str(ROOT / "assets" / "logo.png"), Inches(11.0), Inches(7.02), height=Inches(0.28))


def notes(slide, content):
    slide.notes_slide.notes_text_frame.text = content


def kpi(slide, x, y, w, h, value, label, detail="", color=NAVY):
    box(slide, x, y, w, h, WHITE, line=RGBColor(0xE2, 0xE9, 0xF2))
    text(slide, x + 0.18, y + 0.14, w - 0.36, 0.45, value, size=22, color=color, bold=True)
    text(slide, x + 0.18, y + 0.62, w - 0.36, 0.25, label.upper(), size=8, color=SLATE, bold=True)
    if detail:
        text(slide, x + 0.18, y + 0.86, w - 0.36, 0.25, detail, size=8, color=TEAL)


def image(slide, filename, x, y, w=None, h=None):
    if not filename.exists():
        return
    kwargs = {}
    if w:
        kwargs["width"] = Inches(w)
    if h:
        kwargs["height"] = Inches(h)
    slide.shapes.add_picture(str(filename), Inches(x), Inches(y), **kwargs)


def card(slide, x, y, w, h, heading, body, color=NAVY, fill=WHITE):
    box(slide, x, y, w, h, fill, line=RGBColor(0xE2, 0xE9, 0xF2))
    box(slide, x, y, 0.08, h, _rgb(color), radius=False)
    text(slide, x + 0.22, y + 0.16, w - 0.35, 0.35, heading, size=14, color=color, bold=True)
    text(slide, x + 0.22, y + 0.58, w - 0.35, max(0.05, h - 0.68), body, size=10.5, color=SLATE)


# ---------------------------------------------------------------------------
# 1. Titre
# ---------------------------------------------------------------------------
slide = add_slide(NAVY)
# decorative circles
circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(10.5), Inches(-1.2), Inches(4.2), Inches(4.2))
circle.fill.solid(); circle.fill.fore_color.rgb = RGBColor(0x13, 0x3B, 0x66); circle.line.fill.background()
circle2 = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(11.4), Inches(3.8), Inches(3.2), Inches(3.2))
circle2.fill.solid(); circle2.fill.fore_color.rgb = RGBColor(0x0E, 0x5A, 0x63); circle2.line.fill.background()
image(slide, ROOT / "assets" / "logo.png", 0.8, 0.65, w=3.4)
text(slide, 0.8, 2.0, 11.0, 0.5, "MINI-PROJET FINAL  ·  AGENTIC AI FOR QUANTITATIVE FINANCE", size=11, color=GOLD, bold=True)
text(slide, 0.8, 2.55, 11.4, 1.2, "QuantAgent", size=54, color=WHITE, bold=True)
text(slide, 0.82, 3.72, 10.8, 1.0, "Agent hybride GraphRAG pour l'analyse quantitative,\nla gestion des risques et la conformité", size=21, color=PALE)
text(slide, 0.82, 5.1, 10.5, 0.5, "Vectoriel + Knowledge Graph + quantification + HITL + sécurité", size=13, color=TEAL, bold=True)
text(slide, 0.82, 6.45, 6.0, 0.35, "KAMAL EL AFOUI  ·  Novembre 2026  ·  v1.0.0", size=11, color=PALE)
text(slide, 9.7, 6.45, 3.0, 0.35, "localhost:8007", size=11, color=GOLD, bold=True, align=PP_ALIGN.RIGHT)
notes(slide, "Bonjour. Je présente QuantAgent, un agent hybride GraphRAG pour la finance quantitative. "
             "Le projet répond aux quatre critères : JSON 100 %, agent hybride vecteur + graphe, documentation sécurisée, démo workflow et slides.")

# ---------------------------------------------------------------------------
# 2. Introduction
# ---------------------------------------------------------------------------
slide = add_slide()
title(slide, "Introduction", "Contexte, objectif et démarche du mini-projet final")
card(slide, 0.65, 1.85, 3.85, 2.35, "Contexte", "IA agentique et finance quantitative : le calcul doit être exact, la réponse traçable et la décision doit rester humaine.", NAVY)
card(slide, 4.75, 1.85, 3.85, 2.35, "Objectif", "QuantAgent : agent hybride pour un portefeuille de 250 M€ — questions multi-hop, scénarios, limites et HITL.", GOLD)
card(slide, 8.85, 1.85, 3.85, 2.35, "Démarche", "Corpus → Knowledge Graph → vectoriel → quantification → HITL → JSON → dashboard 8007.", TEAL)
box(slide, 0.65, 4.55, 12.05, 1.25, NAVY)
text(slide, 0.95, 4.72, 11.4, 0.3, "PÉRIMÈTRE DU PROJET", size=9, color=GOLD, bold=True)
text(slide, 0.95, 5.05, 11.4, 0.55, "22 documents · 12 positions · 105 entités · 362 relations · 8 questions · 3 scénarios", size=13, color=WHITE, bold=True)
kpi(slide, 0.65, 5.95, 2.8, 0.65, "250 M€", "NAV", "Core Europe")
kpi(slide, 3.65, 5.95, 2.8, 0.65, "22", "documents", "corpus synthétique")
kpi(slide, 6.65, 5.95, 2.8, 0.65, "105", "entités", "Knowledge Graph")
kpi(slide, 9.65, 5.95, 3.05, 0.65, "8", "questions", "multi-hop")
footer(slide)
notes(slide, "Cette introduction pose le cadre : l'IA agentique appliquée à la finance quantitative exige des garanties de calcul, de traçabilité et de contrôle humain. "
             "Le projet QuantAgent couvre toute la chaîne, du corpus au dashboard 8007, avec un JSON validé et une démonstration reproductible.")

# ---------------------------------------------------------------------------
# 3. Problématique
# ---------------------------------------------------------------------------
slide = add_slide()
title(slide, "Problématique", "Pourquoi un RAG vectoriel ne suffit pas en finance quantitative")
card(slide, 0.65, 1.85, 3.85, 2.3, "Question centrale", "Comment répondre à des questions multi-hop, calculer un impact, vérifier les limites et préparer une décision humaine, avec traçabilité, sécurité et JSON 100 % valide ?", NAVY)
card(slide, 4.75, 1.85, 3.85, 2.3, "Limite du vectoriel", "Il retrouve des passages, mais ne calcule pas le P&L, ne traverse pas les relations et ne déclenche pas les contrôles.", CORAL)
card(slide, 8.85, 1.85, 3.85, 2.3, "Défi de l'agent", "Combiner vectoriel + graphe + quantification + HITL + sécurité, sans jamais exécuter d'ordre.", TEAL)
box(slide, 0.65, 4.55, 12.05, 1.35, NAVY)
text(slide, 0.95, 4.75, 5.6, 0.35, "Le problème n'est pas de trouver un document.", size=16, color=WHITE, bold=True)
text(slide, 0.95, 5.15, 11.4, 0.45, "C'est de relier une position à un facteur, un scénario à une méthode, un résultat à une limite, puis une décision à un humain.", size=13, color=PALE)
kpi(slide, 0.65, 5.95, 2.8, 0.65, "22", "documents", "corpus synthétique")
kpi(slide, 3.65, 5.95, 2.8, 0.65, "105", "entités", "Knowledge Graph")
kpi(slide, 6.65, 5.95, 2.8, 0.65, "8", "questions", "multi-hop")
kpi(slide, 9.65, 5.95, 3.05, 0.65, "100 %", "JSON valide", "100/100")
footer(slide)
notes(slide, "La problématique est volontairement multi-hop. Un RAG classique va citer des documents, mais ne produira pas -8,14 M€, "
             "ne dira pas que la limite de 3 % est dépassée et ne déclenchera pas HITL-RISK. C'est là que l'agent hybride apporte de la valeur.")

# ---------------------------------------------------------------------------
# 3. Cas d'usage multi-hop
# ---------------------------------------------------------------------------
slide = add_slide()
title(slide, "Cas d'usage multi-hop", "Du portefeuille à la décision humaine")
box(slide, 0.65, 1.8, 5.0, 1.55, LIGHT, line=RGBColor(0xE2, 0xE9, 0xF2))
text(slide, 0.9, 1.98, 4.5, 0.3, "QUESTION Q2", size=9, color=GOLD, bold=True)
text(slide, 0.9, 2.28, 4.45, 0.9, "Quel est l'impact d'un choc de +100 pb sur les taux EUR, et quelles positions contribuent le plus ?", size=13, color=NAVY, bold=True)
steps = [
    ("1", "Portefeuille", "PF-CORE-EU", NAVY),
    ("2", "Positions", "POS-01 … POS-12", BLUE),
    ("3", "Facteurs", "Taux EUR · crédit", CORAL),
    ("4", "Scénario", "SCN-RATES-100BP", GOLD),
    ("5", "Limites", "CTL-SCENARIO-LOSS", TEAL),
    ("6", "Décision", "HITL-RISK + HITL-IC", "#059669"),
]
for index, (num, label, detail, color) in enumerate(steps):
    y = 1.8 + index * 0.78
    box(slide, 6.05, y, 0.55, 0.55, color, radius=True)
    text(slide, 6.05, y + 0.1, 0.55, 0.3, num, size=12, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    text(slide, 6.8, y + 0.02, 2.2, 0.28, label, size=11, color=NAVY, bold=True)
    text(slide, 9.0, y + 0.02, 3.7, 0.28, detail, size=10, color=SLATE)
    if index < len(steps) - 1:
        text(slide, 6.22, y + 0.5, 0.2, 0.2, "↓", size=12, color=SLATE, align=PP_ALIGN.CENTER)
box(slide, 0.65, 3.65, 5.0, 2.9, WHITE, line=RGBColor(0xE2, 0xE9, 0xF2))
text(slide, 0.9, 3.82, 4.4, 0.3, "RÉSULTAT ATTENDU", size=9, color=TEAL, bold=True)
text(slide, 0.9, 4.15, 4.45, 0.55, "-8,14 M€", size=32, color=CORAL, bold=True)
text(slide, 0.9, 4.75, 4.45, 0.3, "-3,26 % NAV  ·  dépassement 0,64 M€", size=12, color=NAVY, bold=True)
text(slide, 0.9, 5.15, 4.45, 1.2, "Top contributeurs : Vonovia, EDF, Enel, Bund, AXA.\nStatut : PENDING_APPROVAL.\nPreuves : D04, D05, D21.", size=10.5, color=SLATE)
footer(slide)
notes(slide, "Le raisonnement est matérialisé par six sauts. Le graphe fournit les chemins de preuve, le moteur quantitatif les chiffres, "
             "et la politique HITL le statut de décision. C'est cette chaîne complète qui est évaluée.")

# ---------------------------------------------------------------------------
# 4. Architecture
# ---------------------------------------------------------------------------
slide = add_slide()
title(slide, "Architecture globale", "Séparation des responsabilités et traçabilité de bout en bout")
image(slide, DOCS / "architecture_globale_slide.png", 1.65, 1.6, w=10.0)
footer(slide)
notes(slide, "Le dashboard et l'API sont les points d'entrée. L'orchestrateur route l'intention. La sécurité filtre. "
             "Le vectoriel et le graphe apportent les preuves, le moteur quantitatif calcule, HITL décide, le contrat JSON valide et l'audit conserve.")

# ---------------------------------------------------------------------------
# 5. Agent hybride
# ---------------------------------------------------------------------------
slide = add_slide()
title(slide, "Agent hybride", "Trois moteurs complémentaires, une seule réponse traçable")
card(slide, 0.65, 1.85, 3.85, 2.25, "RAG vectoriel", "TF-IDF documents + phrases\nTop-k passages\nCitations et sources\nBaseline d'évaluation", BLUE)
card(slide, 4.75, 1.85, 3.85, 2.25, "Knowledge Graph", "105 entités · 362 relations\nParcours multi-hop\nChemins de preuve\nExport JSON + Cypher", "#7C3AED")
card(slide, 8.85, 1.85, 3.85, 2.25, "Moteur quantitatif", "Taux · crédit · actions\nP&L et limites\nScénarios paramétrables\nContrôles automatiques", GOLD)
box(slide, 0.65, 4.4, 12.05, 0.9, NAVY)
text(slide, 0.9, 4.55, 11.5, 0.3, "Sécurité → Routage → Retrieval → Graphe → Quantification → HITL → JSON → Audit", size=14, color=WHITE, bold=True)
kpi(slide, 0.65, 5.55, 2.85, 0.85, "5,00 / 5", "score hybride", "8/8 questions")
kpi(slide, 3.65, 5.55, 2.85, 0.85, "1,90 / 5", "score vectoriel", "baseline")
kpi(slide, 6.65, 5.55, 2.85, 0.85, "+3,10", "delta", "hybride vs vectoriel")
kpi(slide, 9.65, 5.55, 3.05, 0.85, "< 300 ms", "latence", "local")
footer(slide)
notes(slide, "Les trois moteurs sont complémentaires. Le vectoriel apporte le contexte documentaire, le graphe la structure, "
             "le quantitatif les chiffres. L'évaluation montre que l'hybride gagne 8 questions sur 8 avec 5,00/5.")

# ---------------------------------------------------------------------------
# 6. Knowledge Graph
# ---------------------------------------------------------------------------
slide = add_slide()
title(slide, "Knowledge Graph", "105 entités, 362 relations, 16 types")
kpi(slide, 0.65, 1.8, 2.5, 0.8, "105", "nœuds", "16 types")
kpi(slide, 3.3, 1.8, 2.5, 0.8, "362", "relations", "25 types")
kpi(slide, 5.95, 1.8, 2.5, 0.8, "0,0321", "densité", "graphe dirigé")
kpi(slide, 8.6, 1.8, 2.5, 0.8, "6,69", "degré moyen", "connexions")
kpi(slide, 11.25, 1.8, 1.45, 0.8, "6", "composantes", "max 100")
image(slide, DOCS / "graph_overview_slide.png", 0.55, 2.85, w=6.3)
card(slide, 7.15, 2.9, 5.55, 3.45, "Types d'entités", "Portefeuille · Position · Émetteur · Secteur · Facteur · Scénario · Politique · Contrôle · Approbation · Réglementation · Risque · Métrique · Document · Watchlist · Comité · Modèle", "#7C3AED")
text(slide, 7.15, 6.5, 5.5, 0.3, "Export JSON + Cypher pour Neo4j", size=9, color=SLATE, italic=True)
footer(slide)
notes(slide, "Le graphe est le squelette du raisonnement. Il permet de passer d'un portefeuille à ses positions, puis aux facteurs, "
             "aux scénarios, aux contrôles et aux approbations. Chaque arête est documentée par un ou plusieurs documents.")

# ---------------------------------------------------------------------------
# 7. Scénario +100 bp
# ---------------------------------------------------------------------------
slide = add_slide()
title(slide, "Scénario +100 bp", "Le chiffre, les contributeurs, la limite")
kpi(slide, 0.65, 1.8, 3.0, 0.95, "-8,14 M€", "impact P&L", "choc +100 bp", CORAL)
kpi(slide, 3.85, 1.8, 3.0, 0.95, "-3,26 %", "impact NAV", "limite 3,0 %", CORAL)
kpi(slide, 7.05, 1.8, 3.0, 0.95, "0,64 M€", "dépassement", "BREACH", CORAL)
kpi(slide, 10.25, 1.8, 2.45, 0.95, "HITL", "statut", "PENDING", GOLD)
image(slide, RESULTS / "fig_scenario_impact.png", 0.55, 2.95, w=6.7)
image(slide, RESULTS / "fig_limit_utilization.png", 7.35, 2.95, w=5.45)
box(slide, 0.65, 6.35, 12.05, 0.55, LIGHT, line=RGBColor(0xE2, 0xE9, 0xF2))
text(slide, 0.9, 6.47, 11.5, 0.3, "Méthode : P&L = -MV × duration × Δy (obligations) ; bêta taux (actions). Sources : D04, D05, D21.", size=9, color=SLATE)
footer(slide)
notes(slide, "Le choc produit -8,14 M€, soit -3,26 % NAV. La limite de 3 % est dépassée de 0,64 M€. "
             "Les cinq premiers contributeurs sont Vonovia, EDF, Enel, Bund et AXA. C'est un cas de dépassement qui déclenche HITL-RISK.")

# ---------------------------------------------------------------------------
# 8. HITL
# ---------------------------------------------------------------------------
slide = add_slide()
title(slide, "Human-in-the-Loop", "Le agent prépare, l'humain décide")
image(slide, DOCS / "workflow_hitl_slide.png", 1.55, 1.55, w=10.2)
card(slide, 0.65, 5.35, 3.85, 1.3, "HITL-RISK", "Dépassement de limite ou impact > 2,5 % NAV. SLA 4 h.", CORAL)
card(slide, 4.75, 5.35, 3.85, 1.3, "HITL-IC", "Opération de portefeuille > 2,5 % NAV. SLA 24 h.", GOLD)
card(slide, 8.85, 5.35, 3.85, 1.3, "HITL-COMPLIANCE", "Client, ESG, PII, watchlist. SLA 24 h.", TEAL)
text(slide, 0.65, 6.78, 12.0, 0.3, "Aucune exécution automatique · journalisation reviewer + timestamp + décision + justification", size=9.5, color=SLATE, italic=True)
footer(slide)
notes(slide, "Le point clé : le agent ne peut pas exécuter un ordre. Il prépare un dossier, identifie les approbations et attend. "
             "Pour une réduction de 10 % de la poche obligataire, HITL-RISK et HITL-IC sont requis. La réduction de 10 % ne suffit pas : il faut environ 19,5 % avec marge.")

# ---------------------------------------------------------------------------
# 9. Sécurité & Red Team
# ---------------------------------------------------------------------------
slide = add_slide()
title(slide, "Sécurité & Red Team", "20 attaques, 20 blocages, 0 faux positif")
kpi(slide, 0.65, 1.8, 3.0, 0.9, "20/20", "attaques bloquées", "100 %", CORAL)
kpi(slide, 3.85, 1.8, 3.0, 0.9, "0/10", "faux positifs", "bénignes", TEAL)
kpi(slide, 7.05, 1.8, 3.0, 0.9, "5", "couches", "défense", NAVY)
kpi(slide, 10.25, 1.8, 2.45, 0.9, "100 %", "JSON", "refus valide", TEAL)
image(slide, DOCS / "security_layers_slide.png", 0.55, 2.9, w=7.0)
card(slide, 7.85, 2.95, 4.85, 3.1, "Catégories couvertes", "Injection de prompt · jailbreak · exfiltration · abus d'outils · ingénierie sociale · conseil financier · contenus nuisibles · poisoning.\n\nDocuments piégés isolés dans data/attack_pack.", CORAL)
text(slide, 0.65, 6.35, 12.0, 0.35, "Filtre d'entrée → isolation documentaire → allowlist d'outils → masquage PII → validation JSON → audit JSONL", size=10, color=SLATE)
footer(slide)
notes(slide, "La sécurité est une défense en profondeur. Les 20 attaques sont bloquées, aucune requête bénigne n'est bloquée. "
             "Les documents piégés ne sont jamais indexés dans le corpus de production.")

# ---------------------------------------------------------------------------
# 10. Dashboard
# ---------------------------------------------------------------------------
slide = add_slide()
title(slide, "Dashboard — localhost:8007", "Menu, formulaire, graphiques, statistiques et journal HITL")
image(slide, DOCS / "dashboard_home.png", 0.55, 1.65, h=4.5)
image(slide, DOCS / "dashboard_agent.png", 8.25, 1.65, h=2.9)
card(slide, 0.65, 6.3, 3.8, 0.65, "Vue d'ensemble", "", NAVY)
card(slide, 4.65, 6.3, 3.8, 0.65, "Agent hybride", "", GOLD)
card(slide, 8.65, 6.3, 4.0, 0.65, "Sécurité & stats", "", TEAL)
footer(slide)
notes(slide, "Le dashboard est le point de démonstration. Il contient le logo, le menu, le formulaire, les graphiques et les statistiques. "
             "On peut poser une question, voir la réponse, le JSON, les chemins de preuve et enregistrer une décision HITL simulée.")

# ---------------------------------------------------------------------------
# 11. Évaluation
# ---------------------------------------------------------------------------
slide = add_slide()
title(slide, "Évaluation", "8 questions, 5 métriques, 8/8 pour l'agent hybride")
image(slide, RESULTS / "fig_comparison.png", 0.55, 1.75, w=6.9)
table_rows = COMPARISON["questions"]
# simple table
rows, cols = len(table_rows) + 1, 6
table_shape = slide.shapes.add_table(rows, cols, Inches(7.7), Inches(1.8), Inches(5.0), Inches(3.8))
table = table_shape.table
headers = ["#", "Difficulté", "Vect.", "Hybride", "Delta", "HITL"]
for c, header in enumerate(headers):
    cell = table.cell(0, c)
    cell.text = header
    cell.fill.solid(); cell.fill.fore_color.rgb = NAVY
    for paragraph in cell.text_frame.paragraphs:
        for run in paragraph.runs:
            run.font.size = Pt(8); run.font.bold = True; run.font.color.rgb = WHITE
for r, row in enumerate(table_rows, start=1):
    values = [row["id"], row["difficulty"], f"{row['vector']['score_global']:.2f}", f"{row['hybrid']['score_global']:.2f}", f"{row['delta']:+.2f}", row["hybrid_hitl"].replace("_", " ")]
    for c, value in enumerate(values):
        cell = table.cell(r, c)
        cell.text = value
        cell.fill.solid(); cell.fill.fore_color.rgb = WHITE if r % 2 else LIGHT
        for paragraph in cell.text_frame.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(7.5); run.font.color.rgb = SLATE
text(slide, 7.7, 5.85, 5.0, 0.35, "Hybride 5,00/5  ·  Vectoriel 1,90/5  ·  Delta +3,10", size=11, color=NAVY, bold=True)
text(slide, 0.65, 5.6, 6.8, 0.5, "Le vectoriel retrouve des passages mais ne calcule pas, ne traverse pas et ne déclenche pas HITL.", size=10, color=SLATE)
footer(slide)
notes(slide, "Le protocole compare les deux approches sur huit questions. L'hybride gagne les huit, avec un score global de 5,00/5. "
             "La différence vient du calcul, des chemins de preuve et du HITL.")

# ---------------------------------------------------------------------------
# 12. JSON contract
# ---------------------------------------------------------------------------
slide = add_slide()
title(slide, "Contrat JSON", "Une sortie unique, validée, citée et auditable")
box(slide, 0.65, 1.75, 7.6, 4.65, RGBColor(0x0F, 0x17, 0x2A), radius=True)
code = '''{
  "request_id": "REQ-...",
  "agent": {"name": "QuantAgent", "mode": "hybrid"},
  "intent": "scenario",
  "answer": "Impact -8,14 M€ ...",
  "confidence": 0.97,
  "entities": ["PF-CORE-EU", "SCN-RATES-100BP"],
  "sources": [{"doc_id": "D21", ...}],
  "graph": {"nodes": [...], "edges": [...], "paths": [...]},
  "quant": {"impact_eur": -8140400, ...},
  "hitl": {"status": "PENDING_APPROVAL", ...},
  "security": {"status": "allowed", ...},
  "trace": [...],
  "meta": {"json_valid": true}
}'''
text(slide, 0.9, 1.95, 7.1, 4.2, code, size=10, color=RGBColor(0xD8, 0xE6, 0xF5), font="Consolas")
kpi(slide, 8.55, 1.8, 4.15, 0.95, "100/100", "JSON valides", "Draft 2020-12", TEAL)
kpi(slide, 8.55, 2.95, 4.15, 0.95, "16", "champs racine", "contrat stable", NAVY)
kpi(slide, 8.55, 4.1, 4.15, 0.95, "0", "erreur de schéma", "validation systématique", TEAL)
text(slide, 8.55, 5.35, 4.15, 0.9, "Chaque réponse est validée avant sortie. Le workflow n8n revalide le contrat.", size=10, color=SLATE)
footer(slide)
notes(slide, "Le JSON est le livrable central. Il contient la réponse, les sources, le graphe, le quantitatif, le HITL, la sécurité et la trace. "
             "Le schéma est Draft 2020-12 et 100 requêtes sur 100 sont valides.")

# ---------------------------------------------------------------------------
# 13. Workflow & Playground
# ---------------------------------------------------------------------------
slide = add_slide()
title(slide, "Workflow & Playground", "Langflow pour la démo interactive, n8n pour l'automatisation")
text(slide, 0.65, 1.72, 7.0, 0.3, "LANGFLOW — QUANTAGENT_FINAL.JSON", size=9, color=GOLD, bold=True)
flow = [
    ("1. Text Input", "question métier", NAVY),
    ("2. QuantAgent API", "Custom Component → POST /ask", BLUE),
    ("3. Text Output", "réponse + JSON + HITL", TEAL),
]
for index, (label, detail, color) in enumerate(flow):
    x = 0.65 + index * 4.0
    box(slide, x, 2.0, 3.5, 0.95, color)
    text(slide, x + 0.12, 2.14, 3.25, 0.3, label, size=12, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    text(slide, x + 0.12, 2.52, 3.25, 0.3, detail, size=8.5, color=WHITE, align=PP_ALIGN.CENTER)
    if index < len(flow) - 1:
        text(slide, x + 3.55, 2.3, 0.35, 0.3, "→", size=18, color=SLATE, align=PP_ALIGN.CENTER)
text(slide, 0.65, 3.25, 7.0, 0.3, "N8N — QUANTAGENT_N8N_FINAL.JSON", size=9, color=GOLD, bold=True)
flow2 = [
    ("Webhook", "POST /quantagent", NAVY),
    ("Validation", "question + mode", NAVY_2),
    ("API", "POST /ask", BLUE),
    ("JSON", "contrat validé", TEAL),
    ("Réponse", "403 / 202 / 200", CORAL),
]
for index, (label, detail, color) in enumerate(flow2):
    x = 0.65 + index * 2.48
    box(slide, x, 3.55, 2.15, 0.8, color)
    text(slide, x + 0.08, 3.67, 2.0, 0.25, label, size=10, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    text(slide, x + 0.08, 3.96, 2.0, 0.25, detail, size=7.5, color=WHITE, align=PP_ALIGN.CENTER)
    if index < len(flow2) - 1:
        text(slide, x + 2.18, 3.78, 0.25, 0.25, "→", size=14, color=SLATE)
box(slide, 0.65, 4.75, 12.05, 1.1, LIGHT, line=RGBColor(0xE2, 0xE9, 0xF2))
text(slide, 0.9, 4.92, 11.5, 0.3, "VIDÉO PLAYGROUND — DOCS/DEMO_PLAYGROUND.MP4 · 56 S", size=9, color=GOLD, bold=True)
text(slide, 0.9, 5.23, 11.5, 0.45, "Dashboard 8007 · formulaire · réponse chiffrée · JSON · HITL · sécurité · statistiques", size=11, color=NAVY, bold=True)
text(slide, 0.65, 6.1, 12.0, 0.45, "Démo : python main.py api puis python main.py serve → Langflow Playground / dashboard 8007", size=10, color=SLATE, italic=True)
footer(slide)
notes(slide, "Deux workflows complémentaires : Langflow pour le Playground interactif (Text Input → Custom Component API → Text Output), "
             "et n8n pour l'automatisation webhook → API → validation JSON → 403/202/200. La vidéo Playground de 56 secondes montre le parcours complet.")

# ---------------------------------------------------------------------------
# 14. Docker / GitHub
# ---------------------------------------------------------------------------
slide = add_slide()
title(slide, "Industrialisation", "Docker, n8n, GitHub Actions et reproductibilité")
card(slide, 0.65, 1.85, 3.85, 2.3, "Docker", "Dashboard 8007\nAPI 8000\nn8n 5678 (profil workflow)\nHealthchecks + volumes", NAVY)
card(slide, 4.75, 1.85, 3.85, 2.3, "GitHub", "Code source\nREADME + tests\nGitHub Actions CI\nDocumentation et slides", "#7C3AED")
card(slide, 8.85, 1.85, 3.85, 2.3, "Reproductibilité", "python main.py demo\npython main.py serve\npytest -q\npython main.py validate --run", TEAL)
box(slide, 0.65, 4.45, 12.05, 1.15, NAVY)
text(slide, 0.9, 4.62, 11.5, 0.3, "LIVRABLES", size=9, color=GOLD, bold=True)
text(slide, 0.9, 4.95, 11.5, 0.45, "JSON Final · main.py · notebook · Docker · dashboard 8007 · architectures · DOCX/PDF · PPTX · GitHub · ZIP", size=12, color=WHITE)
text(slide, 0.65, 5.85, 12.0, 0.4, "github.com/kamalelafoui/agentic-ai-quantitative-finance", size=11, color=BLUE, bold=True)
footer(slide)
notes(slide, "Le projet est industrialisable : Docker pour le dashboard et l'API, n8n pour le workflow, GitHub Actions pour les tests et la validation. "
             "Tout est reproductible avec python main.py demo.")

# ---------------------------------------------------------------------------
# 16. Conclusion
# ---------------------------------------------------------------------------
slide = add_slide(NAVY)
image(slide, ROOT / "assets" / "logo.png", 0.8, 0.55, w=3.3)
text(slide, 0.8, 1.9, 11.5, 0.8, "Conclusion", size=34, color=WHITE, bold=True)
text(slide, 0.82, 2.75, 11.4, 0.5, "Un agent hybride qui ne se contente pas de retrouver : il calcule, relie, contrôle et prépare la décision.", size=15, color=PALE)
text(slide, 0.82, 3.3, 11.4, 0.45, "Le projet répond aux quatre critères : JSON 100 %, agent hybride, documentation sécurisée, démo workflow + slides.", size=11, color=GOLD, bold=True)
items = [
    ("5,00 / 5", "score hybride", GOLD),
    ("8 / 8", "questions gagnées", TEAL),
    ("100 / 100", "JSON valides", TEAL),
    ("20 / 20", "attaques bloquées", CORAL),
    ("0", "faux positif", TEAL),
]
for index, (value, label, color) in enumerate(items):
    x = 0.8 + index * 2.45
    text(slide, x, 4.1, 2.2, 0.55, value, size=25, color=color, bold=True)
    text(slide, x, 4.7, 2.2, 0.3, label.upper(), size=8, color=PALE, bold=True)
text(slide, 0.8, 5.55, 11.5, 0.5, "Perspectives : embeddings denses, Neo4j, backtesting, alertes temps réel, audit réglementaire et signatures HITL.", size=11, color=PALE)
text(slide, 0.8, 6.55, 5.5, 0.35, "KAMAL EL AFOUI  ·  Novembre 2026", size=10, color=PALE)
text(slide, 9.8, 6.55, 2.8, 0.35, "Merci — questions ?", size=12, color=GOLD, bold=True, align=PP_ALIGN.RIGHT)
notes(slide, "En conclusion, QuantAgent répond aux quatre critères : JSON 100 %, agent hybride vecteur + graphe, documentation sécurisée, démo workflow et slides. "
             "Les perspectives sont les embeddings denses, Neo4j, le backtesting, les alertes temps réel et l'audit réglementaire. Merci.")

output = DOCS / "Presentation_Agentic_AI_Quantitative_Finance.pptx"
prs.save(output)
print(output)






