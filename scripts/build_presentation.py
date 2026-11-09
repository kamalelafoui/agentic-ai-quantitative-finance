"""Version courte (5 slides) de la présentation QuantAgent."""

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

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def _rgb(color):
    if isinstance(color, str):
        return RGBColor.from_string(color.replace("#", ""))
    return color


def add_slide(bg=WHITE):
    slide = prs.slides.add_slide(BLANK)
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = bg
    return slide


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


def bullets(slide, x, y, w, h, items, size=13, color=SLATE, spacing=7):
    textbox = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = textbox.text_frame
    frame.word_wrap = True
    frame.margin_left = 0
    frame.margin_right = 0
    for index, item in enumerate(items):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.space_after = Pt(spacing)
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
    box(slide, 0.65, 1.48, 0.75, 0.07, GOLD, radius=False)


def footer(slide):
    page = len(prs.slides)
    text(slide, 0.65, 7.12, 5.5, 0.25, "QuantAgent  ·  Agentic AI for Quantitative Finance", size=8.5, color=SLATE)
    text(slide, 11.4, 7.12, 1.3, 0.25, f"{page:02d}", size=8.5, color=SLATE, align=PP_ALIGN.RIGHT)
    if (ROOT / "assets" / "logo.png").exists():
        slide.shapes.add_picture(str(ROOT / "assets" / "logo.png"), Inches(11.0), Inches(7.02), height=Inches(0.28))


def notes(slide, content):
    slide.notes_slide.notes_text_frame.text = content


def kpi(slide, x, y, w, h, value, label, detail="", color=NAVY):
    box(slide, x, y, w, h, WHITE, line=RGBColor(0xE2, 0xE9, 0xF2))
    text(slide, x + 0.16, y + 0.12, w - 0.3, 0.38, value, size=21, color=color, bold=True)
    text(slide, x + 0.16, y + 0.55, w - 0.3, 0.22, label.upper(), size=7.5, color=SLATE, bold=True)
    if detail:
        text(slide, x + 0.16, y + 0.77, w - 0.3, 0.22, detail, size=7.5, color=TEAL)


def image(slide, filename, x, y, w=None, h=None):
    if not filename.exists():
        return
    kwargs = {}
    if w:
        kwargs["width"] = Inches(w)
    if h:
        kwargs["height"] = Inches(h)
    slide.shapes.add_picture(str(filename), Inches(x), Inches(y), **kwargs)


def card(slide, x, y, w, h, heading, body, color=NAVY):
    box(slide, x, y, w, h, WHITE, line=RGBColor(0xE2, 0xE9, 0xF2))
    box(slide, x, y, 0.08, h, color, radius=False)
    text(slide, x + 0.22, y + 0.14, w - 0.35, 0.3, heading, size=14, color=color, bold=True)
    text(slide, x + 0.22, y + 0.55, w - 0.35, max(0.05, h - 0.65), body, size=10.5, color=SLATE)


# ---------------------------------------------------------------------------
# Slide 1 — Titre
# ---------------------------------------------------------------------------
slide = add_slide(NAVY)
circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(10.5), Inches(-1.2), Inches(4.2), Inches(4.2))
circle.fill.solid(); circle.fill.fore_color.rgb = RGBColor(0x13, 0x3B, 0x66); circle.line.fill.background()
circle2 = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(11.4), Inches(3.8), Inches(3.2), Inches(3.2))
circle2.fill.solid(); circle2.fill.fore_color.rgb = RGBColor(0x0E, 0x5A, 0x63); circle2.line.fill.background()
image(slide, ROOT / "assets" / "logo.png", 0.8, 0.6, w=3.2)
text(slide, 0.8, 1.9, 11.0, 0.4, "MINI-PROJET FINAL  ·  AGENTIC AI FOR QUANTITATIVE FINANCE", size=10.5, color=GOLD, bold=True)
text(slide, 0.8, 2.4, 11.4, 1.0, "QuantAgent", size=52, color=WHITE, bold=True)
text(slide, 0.82, 3.5, 10.8, 0.9, "Agent hybride GraphRAG pour l'analyse quantitative,\nla gestion des risques et la conformité", size=20, color=PALE)
text(slide, 0.82, 4.75, 10.5, 0.4, "Vectoriel + Knowledge Graph + quantification + HITL + sécurité", size=12, color=TEAL, bold=True)
text(slide, 0.82, 5.55, 11.2, 0.4, "5,00/5  ·  8/8 questions  ·  100/100 JSON  ·  20/20 Red Team", size=13, color=GOLD, bold=True)
text(slide, 0.82, 6.55, 6.0, 0.3, "KAMAL EL AFOUI  ·  Novembre 2026  ·  v1.0.0", size=10, color=PALE)
text(slide, 9.7, 6.55, 3.0, 0.3, "localhost:8007", size=10, color=GOLD, bold=True, align=PP_ALIGN.RIGHT)
notes(slide, "Version courte en 5 slides. QuantAgent est un agent hybride GraphRAG pour la finance quantitative : "
             "vectoriel, Knowledge Graph, quantification, HITL et sécurité. Les résultats clés sont 5,00/5, 8/8, 100/100 JSON et 20/20 Red Team.")

# ---------------------------------------------------------------------------
# Slide 2 — Problématique & objectifs
# ---------------------------------------------------------------------------
slide = add_slide()
title(slide, "Problématique & objectifs", "Pourquoi un RAG vectoriel ne suffit pas en finance quantitative")
card(slide, 0.65, 1.8, 3.85, 2.15, "Question centrale", "Comment répondre à des questions multi-hop, calculer un impact, vérifier les limites et préparer une décision humaine, avec traçabilité, sécurité et JSON 100 % valide ?", NAVY)
card(slide, 4.75, 1.8, 3.85, 2.15, "Limite du vectoriel", "Il retrouve des passages, mais ne calcule pas le P&L, ne traverse pas les relations et ne déclenche pas les contrôles.", CORAL)
card(slide, 8.85, 1.8, 3.85, 2.15, "Objectif QuantAgent", "Vectoriel + graphe + quantification + HITL + sécurité, dans un dashboard 8007 et un JSON validé.", TEAL)
box(slide, 0.65, 4.25, 12.05, 1.0, NAVY)
text(slide, 0.9, 4.42, 11.5, 0.3, "4 CRITÈRES DE VALIDATION", size=8.5, color=GOLD, bold=True)
text(slide, 0.9, 4.72, 11.5, 0.35, "JSON 100 %  ·  Agent hybride  ·  Documentation sécurisée  ·  Démo workflow + slides", size=12, color=WHITE, bold=True)
kpi(slide, 0.65, 5.65, 2.85, 0.8, "22", "documents", "corpus synthétique")
kpi(slide, 3.65, 5.65, 2.85, 0.8, "105", "entités", "Knowledge Graph")
kpi(slide, 6.65, 5.65, 2.85, 0.8, "362", "relations", "multi-hop")
kpi(slide, 9.65, 5.65, 3.05, 0.8, "8", "questions", "évaluées")
footer(slide)
notes(slide, "La question centrale est multi-hop : il faut relier portefeuille, positions, facteurs, scénario, limites et décision. "
             "Un RAG vectoriel retrouve des passages mais ne calcule pas et ne déclenche pas HITL. QuantAgent comble ces manques.")

# ---------------------------------------------------------------------------
# Slide 3 — Architecture & agent
# ---------------------------------------------------------------------------
slide = add_slide()
title(slide, "Architecture & agent hybride", "Une seule réponse, trois moteurs et deux garde-fous")
image(slide, DOCS / "architecture_globale_slide.png", 0.55, 1.65, w=8.4)
card(slide, 9.2, 1.7, 3.5, 1.0, "RAG vectoriel", "TF-IDF + citations", BLUE)
card(slide, 9.2, 2.85, 3.5, 1.0, "Knowledge Graph", "105 entités · 362 relations", "#7C3AED")
card(slide, 9.2, 4.0, 3.5, 1.0, "Moteur quantitatif", "P&L · limites · scénarios", GOLD)
card(slide, 9.2, 5.15, 3.5, 1.0, "HITL + sécurité", "Risk / IC / Compliance", "#059669")
box(slide, 0.65, 6.35, 12.05, 0.5, LIGHT, line=RGBColor(0xE2, 0xE9, 0xF2))
text(slide, 0.9, 6.47, 11.5, 0.25, "Sécurité → Routage → Retrieval → Graphe → Quantification → HITL → JSON → Audit", size=9.5, color=NAVY, bold=True)
footer(slide)
notes(slide, "L'architecture sépare les responsabilités : sécurité, routage, vectoriel, graphe, quantification, HITL, contrat JSON et audit. "
             "Le agent prépare un dossier ; il n'exécute jamais d'ordre.")

# ---------------------------------------------------------------------------
# Slide 4 — Résultats
# ---------------------------------------------------------------------------
slide = add_slide()
title(slide, "Résultats", "Scénario +100 bp · évaluation · sécurité")
kpi(slide, 0.65, 1.7, 2.3, 0.85, "-8,14 M€", "impact P&L", "choc +100 bp", CORAL)
kpi(slide, 3.1, 1.7, 2.3, 0.85, "-3,26 %", "impact NAV", "limite 3,0 %", CORAL)
kpi(slide, 5.55, 1.7, 2.3, 0.85, "5,00/5", "score hybride", "8/8 questions", TEAL)
kpi(slide, 8.0, 1.7, 2.3, 0.85, "100/100", "JSON valides", "Draft 2020-12", TEAL)
kpi(slide, 10.45, 1.7, 2.25, 0.85, "20/20", "Red Team", "0 faux positif", CORAL)
image(slide, RESULTS / "fig_scenario_impact.png", 0.55, 2.85, w=6.0)
image(slide, RESULTS / "fig_comparison.png", 6.8, 2.85, w=5.95)
box(slide, 0.65, 6.35, 12.05, 0.5, NAVY)
text(slide, 0.9, 6.47, 11.5, 0.25, "Limite 3,0 % dépassée de 0,64 M€  ·  HITL-RISK + HITL-IC  ·  aucune exécution automatique", size=9.5, color=WHITE, bold=True)
footer(slide)
notes(slide, "Le scénario +100 bp produit -8,14 M€, soit -3,26 % NAV, avec un dépassement de 0,64 M€. "
             "L'agent hybride obtient 5,00/5 contre 1,90/5 pour le vectoriel, 100/100 JSON et 20/20 en Red Team.")

# ---------------------------------------------------------------------------
# Slide 5 — Conclusion & démo
# ---------------------------------------------------------------------------
slide = add_slide()
title(slide, "Conclusion & démo", "Un agent qui calcule, relie, contrôle et prépare la décision")
bullets(slide, 0.65, 1.85, 6.3, 3.4, [
    "8/8 questions · 5,00/5 vs 1,90/5 pour le vectoriel",
    "100/100 JSON valides · 20/20 attaques bloquées · 0 faux positif",
    "HITL Risk / IC / Compliance · aucune exécution automatique",
    "Dashboard 8007 · API 8000 · Langflow + n8n · Docker · GitHub",
], size=13, color=SLATE, spacing=12)
image(slide, DOCS / "demo_playground_poster.png", 7.1, 1.75, w=5.55)
box(slide, 7.1, 5.2, 5.55, 0.55, LIGHT, line=RGBColor(0xE2, 0xE9, 0xF2))
text(slide, 7.3, 5.33, 5.2, 0.25, "Vidéo Playground : docs/demo_playground.mp4 (56 s)", size=9, color=NAVY, bold=True)
text(slide, 0.65, 5.55, 6.2, 0.35, "github.com/kamalelafoui/agentic-ai-quantitative-finance", size=10.5, color=BLUE, bold=True)
text(slide, 0.65, 6.55, 6.0, 0.3, "KAMAL EL AFOUI  ·  Novembre 2026", size=10, color=SLATE)
text(slide, 9.7, 6.55, 3.0, 0.3, "Merci — questions ?", size=12, color=GOLD, bold=True, align=PP_ALIGN.RIGHT)
footer(slide)
notes(slide, "Conclusion : QuantAgent répond aux quatre critères. Les perspectives sont les embeddings denses, Neo4j, le backtesting, "
             "les alertes temps réel et l'audit réglementaire. Merci.")

output = DOCS / "Presentation_Agentic_AI_Quantitative_Finance.pptx"
prs.save(output)
print(output)
print("slides", len(prs.slides))
