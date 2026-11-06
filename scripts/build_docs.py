"""Génère la documentation DOCX de QuantAgent."""

from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
RESULTS = ROOT / "results"
DATA = ROOT / "data"

NAVY = RGBColor(0x0B, 0x25, 0x45)
GOLD = RGBColor(0xF2, 0xC2, 0x30)
TEAL = RGBColor(0x2E, 0xC4, 0xB6)
CORAL = RGBColor(0xE4, 0x57, 0x2E)
SLATE = RGBColor(0x5B, 0x67, 0x78)
LIGHT = RGBColor(0xF4, 0xF7, 0xFB)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

STATS = json.loads((RESULTS / "stats.json").read_text(encoding="utf-8"))
COMPARISON = json.loads((RESULTS / "comparison.json").read_text(encoding="utf-8"))
REDTEAM = json.loads((RESULTS / "red_team.json").read_text(encoding="utf-8"))
VALIDATION = json.loads((RESULTS / "validation_report.json").read_text(encoding="utf-8"))
PORTFOLIO = json.loads((DATA / "portfolio.json").read_text(encoding="utf-8"))
QUESTIONS = json.loads((DATA / "questions.json").read_text(encoding="utf-8"))
SHOWCASE = json.loads((RESULTS / "JSON_Final.json").read_text(encoding="utf-8"))


def shade(cell, color: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), color.replace("#", ""))
    tc_pr.append(shd)


def set_cell_margins(cell, top=80, bottom=80, left=100, right=100):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def add_table(doc, headers, rows, widths=None, font_size=8.5, header_color="0B2545", first_col_bold=False):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for index, header in enumerate(headers):
        hdr[index].text = ""
        paragraph = hdr[index].paragraphs[0]
        run = paragraph.add_run(str(header))
        run.bold = True
        run.font.size = Pt(font_size)
        run.font.color.rgb = WHITE
        shade(hdr[index], header_color)
        set_cell_margins(hdr[index])
    for row_index, row in enumerate(rows):
        cells = table.add_row().cells
        for col_index, value in enumerate(row):
            cells[col_index].text = ""
            paragraph = cells[col_index].paragraphs[0]
            run = paragraph.add_run(str(value))
            run.font.size = Pt(font_size)
            run.font.color.rgb = NAVY if col_index == 0 else SLATE
            if first_col_bold and col_index == 0:
                run.bold = True
            if row_index % 2 == 1:
                shade(cells[col_index], "F4F7FB")
            set_cell_margins(cells[col_index])
    if widths:
        for row in table.rows:
            for index, width in enumerate(widths):
                row.cells[index].width = Cm(width)
    doc.add_paragraph()
    return table


def add_caption(doc, text):
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(text)
    run.italic = True
    run.font.size = Pt(8)
    run.font.color.rgb = SLATE


def add_image(doc, filename: Path, width_inches=6.4, caption=""):
    if not filename.exists():
        return
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if caption:
        paragraph.paragraph_format.keep_with_next = True
    paragraph.add_run().add_picture(str(filename), width=Inches(width_inches))
    if caption:
        add_caption(doc, caption)


def add_code(doc, code: str):
    table = doc.add_table(rows=1, cols=1)
    table.style = "Table Grid"
    cell = table.rows[0].cells[0]
    shade(cell, "F1F5F9")
    set_cell_margins(cell, 100, 100, 140, 140)
    paragraph = cell.paragraphs[0]
    run = paragraph.add_run(code)
    run.font.name = "Consolas"
    run.font.size = Pt(8)
    run.font.color.rgb = NAVY
    doc.add_paragraph()


def add_bullets(doc, items):
    for item in items:
        paragraph = doc.add_paragraph(item, style="List Bullet")
        paragraph.paragraph_format.space_after = Pt(3)


def add_page_number(paragraph):
    run = paragraph.add_run()
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = "PAGE"
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char1)
    run._r.append(instr_text)
    run._r.append(fld_char2)


def style_document(doc):
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Segoe UI"
    normal.font.size = Pt(10)
    normal.font.color.rgb = RGBColor(0x33, 0x3F, 0x50)
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.12
    for level, size, color in [("Heading 1", 17, NAVY), ("Heading 2", 13, NAVY), ("Heading 3", 11, SLATE)]:
        style = styles[level]
        style.font.name = "Segoe UI"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = color
        style.paragraph_format.space_before = Pt(12 if level == "Heading 1" else 8)
        style.paragraph_format.space_after = Pt(5)
    for section in doc.sections:
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(1.8)
        section.left_margin = Cm(2.1)
        section.right_margin = Cm(2.1)


def add_header_footer(doc):
    for section in doc.sections:
        header = section.header
        paragraph = header.paragraphs[0]
        paragraph.text = ""
        run = paragraph.add_run("QuantAgent  ·  Agentic AI for Quantitative Finance")
        run.font.size = Pt(8)
        run.font.color.rgb = SLATE
        paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        footer = section.footer
        paragraph = footer.paragraphs[0]
        paragraph.text = ""
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run("KAMAL EL AFOUI  ·  Mini-projet final  ·  Novembre 2026  ·  page ")
        run.font.size = Pt(8)
        run.font.color.rgb = SLATE
        add_page_number(paragraph)


def cover(doc):
    doc.add_paragraph()
    doc.add_paragraph()
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run().add_picture(str(ROOT / "assets" / "logo.png"), width=Inches(3.7))
    doc.add_paragraph()
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("Agentic AI for Quantitative Finance")
    run.font.size = Pt(30)
    run.font.bold = True
    run.font.color.rgb = NAVY
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("QuantAgent — Agent hybride GraphRAG, quantification, HITL et sécurité")
    run.font.size = Pt(14)
    run.font.color.rgb = GOLD
    doc.add_paragraph()
    # band
    band = doc.add_table(rows=1, cols=1)
    band.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = band.rows[0].cells[0]
    shade(cell, "0B2545")
    set_cell_margins(cell, 180, 180, 180, 180)
    paragraph = cell.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("DOCUMENTATION TECHNIQUE ET FONCTIONNELLE")
    run.font.size = Pt(11)
    run.font.bold = True
    run.font.color.rgb = WHITE
    doc.add_paragraph()
    meta = [
        ("Auteur", "KAMAL EL AFOUI"),
        ("Programme", "Agentic AI for Quantitative Finance — Mini-projet final"),
        ("Édition", "Novembre 2026 · Version 1.0.0"),
        ("Livrable", "Documentation sécurisée — DOCX + PDF"),
        ("Dépôt", "github.com/kamalelafoui/agentic-ai-quantitative-finance"),
    ]
    table = doc.add_table(rows=0, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for key, value in meta:
        cells = table.add_row().cells
        cells[0].text = key
        cells[1].text = value
        for cell in cells:
            set_cell_margins(cell, 60, 60, 100, 100)
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9.5)
                    run.font.color.rgb = NAVY if cell is cells[0] else SLATE
        for run in cells[0].paragraphs[0].runs:
            run.bold = True
    doc.add_paragraph()
    note = doc.add_paragraph()
    note.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = note.add_run("Données fictives · Démonstration pédagogique · Aucun conseil en investissement")
    run.font.size = Pt(8)
    run.font.color.rgb = SLATE
    doc.add_page_break()


def main():
    DOCS.mkdir(exist_ok=True)
    doc = Document()
    style_document(doc)
    add_header_footer(doc)
    cover(doc)

    # Résumé exécutif
    doc.add_heading("Résumé exécutif", level=1)
    doc.add_paragraph(
        "QuantAgent est un agent hybride conçu pour répondre à des questions financières multi-hop "
        "qui exigent de croiser des positions, des facteurs de risque, des scénarios, des politiques et des contrôles. "
        "Il combine une recherche vectorielle TF-IDF, un graphe de connaissances de 105 entités et 362 relations, "
        "un moteur quantitatif de scénarios, des garde-fous de sécurité et une validation humaine HITL. "
        "La sortie est un JSON validé contre un schéma Draft 2020-12."
    )
    add_table(
        doc,
        ["Indicateur", "Valeur", "Commentaire"],
        [
            ("Documents", "22", "Corpus financier synthétique annoté"),
            ("Positions", "12", "NAV 250 M€ — Core Europe"),
            ("Entités / relations", "105 / 362", "Knowledge Graph NetworkX"),
            ("Questions évaluées", "8", "Simple, multi-hop, intersection, policy, red-team"),
            ("Score hybride", f"{COMPARISON['aggregates']['hybrid']['score_global']:.2f} / 5", "8/8 questions"),
            ("Score vectoriel", f"{COMPARISON['aggregates']['vector']['score_global']:.2f} / 5", "Baseline TF-IDF"),
            ("JSON valide", f"{VALIDATION['valid']}/{VALIDATION['total']}", "Schéma Draft 2020-12"),
            ("Red Team", f"{REDTEAM['blocked']}/{REDTEAM['total_attacks']}", "0 faux positif"),
        ],
        widths=[4.2, 3.5, 8.5],
    )
    add_image(doc, DOCS / "dashboard_home.png", 6.4)

    # Sommaire
    doc.add_heading("Sommaire", level=1)
    sections = [
        "Introduction",
        "1. Problématique",
        "2. Objectifs et critères de validation",
        "3. Cas d'usage multi-hop",
        "4. Corpus et données",
        "5. Architecture globale",
        "6. Agent hybride : vectoriel, graphe et quantification",
        "7. Knowledge Graph",
        "8. Analyse quantitative et limites",
        "9. Human-in-the-Loop",
        "10. Sécurité et Red Team",
        "11. Dashboard et API",
        "12. Évaluation",
        "13. Conclusion",
        "14. Reproductibilité, Docker, n8n et GitHub",
        "15. Limites et perspectives",
        "16. Annexes",
    ]
    for section in sections:
        paragraph = doc.add_paragraph(section)
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph.paragraph_format.left_indent = Cm(0.4)
    doc.add_paragraph()
    doc.add_heading("Comment lire ce document", level=2)
    doc.add_paragraph(
        "L'introduction et la section 1 posent le contexte et la question centrale. Les sections 2 à 5 précisent "
        "les objectifs, le cas d'usage, les données et l'architecture. Les sections 6 à 11 décrivent l'agent hybride, "
        "le graphe, le moteur quantitatif, le HITL, la sécurité et le dashboard. La section 12 présente l'évaluation, "
        "la section 13 synthétise les résultats, et les sections 14 à 16 couvrent la reproductibilité, les limites et les annexes."
    )
    doc.add_page_break()

    # Introduction
    doc.add_heading("Introduction", level=1)
    doc.add_paragraph(
        "L'intelligence artificielle agentique transforme la manière dont les équipes financières interrogent leurs "
        "données. Un agent ne se contente plus de retrouver un document : il planifie, appelle des outils, croise des "
        "sources et prépare une décision. En finance quantitative, cette promesse se heurte toutefois à trois exigences "
        "non négociables : le calcul doit être exact, la réponse doit être traçable, et la décision doit rester humaine."
    )
    doc.add_paragraph(
        "Ce mini-projet final conçoit et évalue QuantAgent, un agent hybride pour l'analyse quantitative, la gestion "
        "des risques et la conformité. Le cas d'usage est un portefeuille européen de 250 M€ : l'agent doit répondre à "
        "des questions multi-hop, calculer l'impact d'un choc de taux ou de crédit, vérifier les limites, citer ses "
        "sources et préparer un dossier HITL. Le projet couvre l'ensemble de la chaîne : corpus, Knowledge Graph, "
        "RAG vectoriel, moteur quantitatif, sécurité, dashboard, API, Docker, notebook, documentation et présentation."
    )
    doc.add_paragraph("Les contributions principales sont les suivantes :")
    add_bullets(doc, [
        "Une architecture hybride qui combine recherche vectorielle TF-IDF, parcours multi-hop sur graphe et calcul quantitatif.",
        "Un moteur de scénarios et de limites qui produit des chiffres vérifiables, avec des chemins de preuve et des citations.",
        "Une couche de sécurité et un contrat JSON validé à 100 %, avec un workflow HITL Risk / Comité / Compliance.",
        "Un dashboard Streamlit sur le port 8007, une API FastAPI, un workflow n8n et une documentation complète.",
    ])
    doc.add_paragraph(
        "Le document est organisé en trois temps : la problématique et les objectifs, la conception et l'implémentation, "
        "puis l'évaluation et la conclusion. Les données sont fictives et le projet est pédagogique ; aucune sortie ne "
        "constitue un conseil en investissement."
    )

    # 1. Problématique
    doc.add_heading("1. Problématique", level=1)
    doc.add_paragraph(
        "Les équipes de gestion quantitative doivent répondre à des questions qui ne se réduisent pas à une recherche "
        "documentaire. Une question comme « quel est l'impact d'un choc de +100 pb sur les taux, et quelles positions "
        "contribuent le plus ? » exige de relier un portefeuille à ses positions, les positions à leurs facteurs de "
        "risque, le scénario à une méthode de calcul, puis le résultat à des limites et à un circuit d'approbation."
    )
    doc.add_paragraph(
        "Un RAG vectoriel classique retrouve des passages pertinents, mais ne calcule pas le P&L, ne traverse pas les "
        "relations et ne déclenche pas les contrôles. QuantAgent répond à cette limite en combinant trois capacités : "
        "la récupération sémantique, le raisonnement multi-hop sur graphe et le calcul quantitatif."
    )
    add_table(
        doc,
        ["Élément", "Formulation"],
        [
            ("Question centrale", "Comment concevoir un agent capable de répondre à des questions financières multi-hop, de calculer un impact, de vérifier les limites et de préparer une décision humaine, tout en garantissant traçabilité, sécurité et JSON 100 % valide ?"),
            ("Sous-question 1", "Comment combiner recherche vectorielle et Knowledge Graph pour couvrir les questions multi-hop ?"),
            ("Sous-question 2", "Comment calculer le P&L, vérifier les limites et produire des chiffres auditables ?"),
            ("Sous-question 3", "Comment intégrer HITL, sécurité et contrat JSON sans bloquer l'usage ?"),
            ("Sous-question 4", "Comment démontrer la valeur de l'agent face à une baseline vectorielle ?"),
        ],
        widths=[3.5, 12.5],
    )
    add_bullets(doc, [
        "Problème métier : analyser un portefeuille sous stress, vérifier les limites et préparer une décision humaine.",
        "Contrainte : produire une réponse traçable, chiffrée, sécurisée et validable par un humain.",
        "Contrainte technique : sortie JSON 100 % valide, reproductible et testable.",
    ])

    # 2. Objectifs
    doc.add_heading("2. Objectifs et critères de validation", level=1)
    doc.add_paragraph("Le projet répond aux quatre critères de validation du mini-projet final :")
    add_table(
        doc,
        ["Critère", "Réponse QuantAgent", "Preuve"],
        [
            ("Format : JSON valide à 100 %", "Schéma Draft 2020-12 + validation systématique", f"{VALIDATION['valid']}/{VALIDATION['total']} requêtes valides"),
            ("Agent hybride vecteur + graphe", "TF-IDF + NetworkX + moteur quantitatif", f"{COMPARISON['aggregates']['hybrid']['score_global']:.2f}/5 · 8/8"),
            ("Documentation sécurisée complète", "DOCX + PDF + politique de sécurité + Red Team", "20/20 attaques bloquées"),
            ("Démo workflow + slides", "Dashboard port 8007 + PPTX + n8n", "Captures + vidéo de démonstration"),
        ],
        widths=[4.5, 7.0, 5.0],
    )

    # 3. Cas d'usage
    doc.add_heading("3. Cas d'usage multi-hop", level=1)
    doc.add_paragraph(
        "Le cas de référence est le scénario SCN-RATES-100BP appliqué au portefeuille PF-CORE-EU. "
        "La question Q2 demande l'impact et les principaux contributeurs. Le raisonnement traverse quatre familles "
        "de nœuds : portefeuille, positions, facteurs de risque et politiques."
    )
    add_table(
        doc,
        ["Étape", "Question", "Nœuds traversés"],
        [
            ("1", "Quel portefeuille ?", "PF-CORE-EU"),
            ("2", "Quelles positions ?", "POS-01 … POS-12"),
            ("3", "Quels facteurs ?", "FACTOR-EUR-RATES, FACTOR-CREDIT-SPREAD"),
            ("4", "Quel scénario ?", "SCN-RATES-100BP"),
            ("5", "Quelles limites ?", "CTL-SCENARIO-LOSS, CTL-ISSUER-CAP…"),
            ("6", "Quelle décision ?", "POL-HITL → HITL-RISK / HITL-IC"),
        ],
        widths=[2.0, 5.0, 9.0],
    )
    add_code(doc, "Question Q2 : Quel est l'impact estimé d'un choc de +100 pb sur les taux EUR\n"
                  "pour le portefeuille Core Europe, et quelles positions contribuent le plus ?\n\n"
                  "Réponse : -8,14 M€ (-3,26 % NAV) ; Vonovia, EDF, Enel, Bund et AXA ;\n"
                  "limite 3,0 % dépassée de 0,64 M€ ; HITL-RISK + HITL-IC requis.")

    # 4. Corpus
    doc.add_heading("4. Corpus et données", level=1)
    doc.add_paragraph(
        "Le corpus contient 22 documents synthétiques : mandat, reporting, politiques, méthodologies, notes de recherche, "
        "PV de comité, glossaire et référentiel d'instruments. Les documents sont classifiés (Public, Interne, Restricted, "
        "Confidentiel) et annotés avec les entités du graphe."
    )
    add_table(
        doc,
        ["Famille", "Exemples", "Nombre"],
        [
            ("Mandat & reporting", "D01, D02, D21", "3"),
            ("Politiques & procédures", "D03, D07, D08, D09, D10, D15, D16, D17", "8"),
            ("Méthodologie & scénarios", "D04, D05, D19, D22", "4"),
            ("Notes de recherche", "D12, D13, D14", "3"),
            ("Comité & référentiels", "D11, D20", "2"),
            ("Sécurité", "D18", "1"),
        ],
        widths=[4.5, 8.0, 3.0],
    )
    add_table(
        doc,
        ["Position", "Classe", "Secteur", "Valeur (M€)", "Poids", "Sensibilité taux"],
        [
            (p["name"], p["asset_class"], p["sector_id"].replace("SEC-", ""), f"{p['market_value_eur']/1e6:.1f}", f"{p['weight_pct']:.1f}%",
             f"duration {p['modified_duration']:.1f}" if p["asset_class"] == "Obligation" else f"{p['rate_beta_pct_per_bp']:+.3f} %/bp")
            for p in PORTFOLIO["positions"]
        ],
        widths=[5.0, 2.0, 2.5, 2.2, 1.8, 3.0],
        font_size=7.8,
    )

    # 5. Architecture
    doc.add_heading("5. Architecture globale", level=1)
    doc.add_paragraph(
        "L'architecture sépare les responsabilités : le dashboard et l'API exposent le service, l'orchestrateur route "
        "l'intention, la sécurité filtre l'entrée, le vectoriel et le graphe fournissent les preuves, le moteur "
        "quantitatif calcule, la politique HITL décide du circuit, le contrat JSON valide la sortie et l'audit conserve "
        "les traces."
    )
    add_image(doc, DOCS / "architecture_globale.png", 6.4, "Figure 1 — Architecture globale de QuantAgent")
    add_image(doc, DOCS / "architecture_agent.png", 6.4, "Figure 2 — Boucle de l'agent en 9 étapes")

    # 6. Agent hybride
    doc.add_heading("6. Agent hybride : vectoriel, graphe et quantification", level=1)
    doc.add_heading("6.1 Recherche vectorielle", level=2)
    doc.add_paragraph(
        "L'index TF-IDF est construit sur les documents et les phrases. La recherche retourne les top-k documents et "
        "les passages les plus proches. La baseline est volontairement simple : elle ne calcule pas, ne traverse pas "
        "le graphe et ne déclenche pas HITL. Elle sert de point de comparaison."
    )
    doc.add_heading("6.2 Knowledge Graph", level=2)
    doc.add_paragraph(
        "Le graphe est un NetworkX DiGraph. Les entités sont typées (Portefeuille, Position, Émetteur, Secteur, "
        "Facteur, Scénario, Politique, Contrôle, Approbation, Réglementation, Risque, Métrique, Document, Watchlist, "
        "Comité, Modèle). Les relations sont typées et documentées (HOLDS, SENSITIVE_TO, CONSTRAINED_BY, "
        "REQUIRES_APPROVAL, GOVERNED_BY, WATCHLISTED_BY, etc.)."
    )
    add_table(
        doc,
        ["Type d'entité", "Nombre", "Exemples"],
        [(key, value, ", ".join([n["label"] for n in json.loads((DATA / "nodes.json").read_text(encoding="utf-8")) if n["type"] == key][:3])) for key, value in STATS["graph"]["node_types"].items()],
        widths=[4.0, 2.0, 9.0],
        font_size=7.8,
    )
    add_image(doc, DOCS / "graph_overview.png", 6.4, "Figure 3 — Vue simplifiée du graphe de connaissances")
    doc.add_heading("6.3 Moteur quantitatif", level=2)
    doc.add_paragraph(
        "Le moteur applique trois familles de chocs : taux, crédit et actions. Pour les obligations, le P&L est calculé "
        "par -MV × duration modifiée × Δy. Pour les actions, un bêta taux en %/bp est utilisé. Le scénario crédit "
        "utilise un DV01 de spread. Les limites sont ensuite vérifiées : perte scénario, concentration émetteur, "
        "concentration secteur, liquidité T+1, duration et VaR."
    )

    # 7. Knowledge Graph
    doc.add_heading("7. Knowledge Graph", level=1)
    doc.add_paragraph(
        "Le graphe contient 105 nœuds et 362 relations. Il est exporté en JSON et en Cypher pour une exploration Neo4j. "
        "Les chemins de preuve sont retournés dans chaque réponse JSON."
    )
    add_table(
        doc,
        ["Métrique", "Valeur"],
        [
            ("Nœuds", STATS["graph"]["nodes"]),
            ("Relations", STATS["graph"]["edges"]),
            ("Densité", STATS["graph"]["density"]),
            ("Composantes", STATS["graph"]["components"]),
            ("Degré moyen", STATS["graph"]["avg_degree"]),
            ("Plus grande composante", STATS["graph"]["largest_component"]),
        ],
        widths=[6.0, 4.0],
    )
    add_table(
        doc,
        ["Nœud", "Type", "Degré"],
        [(row["label"], row["type"], row["degree"]) for row in STATS["graph"]["top_nodes"]],
        widths=[8.0, 4.0, 2.0],
        font_size=8,
    )

    # 8. Analyse quantitative
    doc.add_heading("8. Analyse quantitative et limites", level=1)
    scenario = SHOWCASE["quant"]
    doc.add_paragraph(
        f"Le scénario {scenario['scenario']['id']} applique un choc de +100 pb. "
        f"L'impact estimé est de {scenario['impact_eur']/1e6:+.2f} M€, soit {scenario['impact_pct_nav']:+.2f} % de la NAV. "
        f"La NAV passerait de 250,00 M€ à {scenario['nav_after_eur']/1e6:.2f} M€."
    )
    add_table(
        doc,
        ["Position", "Impact (M€)", "Impact % NAV", "Driver"],
        [(row["name"], f"{row['impact_eur']/1e6:+.2f}", f"{row['impact_pct_nav']:+.2f} %", row["driver"]) for row in scenario["top_contributors"][:6]],
        widths=[6.0, 3.0, 3.0, 4.0],
    )
    add_table(
        doc,
        ["Contrôle", "Valeur", "Limite", "Statut"],
        [(check["name"], f"{check['value']:.2f} {check['unit']}", f"{check['limit']:.2f} {check['unit']}", check["status"]) for check in scenario["limit_checks"]],
        widths=[6.0, 3.5, 3.5, 3.0],
    )
    add_image(doc, RESULTS / "fig_scenario_impact.png", 6.4, "Figure 4 — Contributeurs au scénario de taux")
    add_image(doc, RESULTS / "fig_limit_utilization.png", 6.4, "Figure 5 — Utilisation des limites")

    # 9. HITL
    doc.add_heading("9. Human-in-the-Loop", level=1)
    doc.add_paragraph(
        "Le agent ne peut jamais exécuter un ordre. Il prépare un dossier, identifie les approbations requises et attend "
        "une décision humaine. La politique POL-HITL définit les seuils et les délais. Le statut par défaut est "
        "PENDING_APPROVAL."
    )
    add_image(doc, DOCS / "workflow_hitl.png", 6.4, "Figure 6 — Workflow HITL")
    add_table(
        doc,
        ["Approbation", "Rôle", "Déclencheur", "SLA"],
        [
            ("HITL-RISK", "Risk Manager", "Dépassement de limite / impact > 2,5 % NAV", "4 h"),
            ("HITL-IC", "Comité d'Investissement", "Opération > 2,5 % NAV", "24 h"),
            ("HITL-COMPLIANCE", "Compliance Officer", "Client, ESG, PII, watchlist", "24 h"),
            ("HITL-MODEL", "Model Risk Officer", "Changement de modèle", "48 h"),
        ],
        widths=[4.0, 4.0, 7.0, 2.0],
    )
    doc.add_paragraph(
        "Pour Q4, une réduction de 10 % de la poche obligataire (6,4 M€) nécessite HITL-RISK et HITL-IC. "
        "Cette réduction ne suffit pas : la perte scénario resterait à -3,11 % NAV. Il faut environ 19,5 % "
        "avec marge opérationnelle pour repasser sous 3,0 %."
    )

    # 10. Sécurité
    doc.add_heading("10. Sécurité et Red Team", level=1)
    doc.add_paragraph(
        "La sécurité est une défense en profondeur : filtre d'entrée, isolation documentaire, allowlist d'outils, "
        "masquage PII, validation JSON et journal d'audit. Les documents piégés sont stockés dans data/attack_pack "
        "et ne sont jamais indexés."
    )
    add_image(doc, DOCS / "security_layers.png", 6.4, "Figure 7 — Défense en profondeur")
    add_table(
        doc,
        ["Catégorie", "Attaques", "Bloquées", "Taux"],
        [(key, value["total"], value["blocked"], f"{value['blocked']/max(value['total'],1)*100:.0f} %") for key, value in REDTEAM["categories"].items()],
        widths=[5.0, 3.0, 3.0, 3.0],
    )
    add_table(
        doc,
        ["ID", "Catégorie", "Statut", "Risque", "Flags"],
        [(row["id"], row["category"], row["status"], f"{row['risk_score']:.2f}", ", ".join(row["flags"])) for row in REDTEAM["attacks"][:10]],
        widths=[2.0, 3.5, 2.5, 2.0, 6.0],
        font_size=7.5,
    )
    doc.add_paragraph(
        f"Résultat : {REDTEAM['blocked']}/{REDTEAM['total_attacks']} attaques bloquées, "
        f"{REDTEAM['false_positives']} faux positif sur {REDTEAM['benign_total']} requêtes bénignes."
    )

    # 11. Dashboard & API
    doc.add_heading("11. Dashboard et API", level=1)
    doc.add_paragraph(
        "Le dashboard Streamlit est exposé sur http://localhost:8007. Il propose un menu, un formulaire, des graphiques, "
        "des statistiques, le graphe interactif, la page sécurité et les téléchargements. L'API FastAPI expose les "
        "mêmes capacités pour l'intégration n8n ou un autre client."
    )
    add_image(doc, DOCS / "dashboard_agent.png", 6.4, "Figure 8 — Formulaire et réponse de l'agent")
    add_image(doc, DOCS / "dashboard_security.png", 6.4, "Figure 9 — Page Sécurité & Red Team")
    add_table(
        doc,
        ["Endpoint", "Méthode", "Description"],
        [
            ("/health", "GET", "État du service"),
            ("/ask", "POST", "Question → JSON QuantAgent"),
            ("/stats", "GET", "Statistiques consolidées"),
            ("/questions", "GET", "Questions d'évaluation"),
            ("/graph", "GET", "Export du graphe"),
            ("/redteam", "GET", "Rapport Red Team"),
            ("/hitl/decision", "POST", "Journaliser une décision humaine"),
        ],
        widths=[3.5, 2.0, 10.0],
    )

    # 12. Évaluation
    doc.add_heading("12. Évaluation", level=1)
    doc.add_paragraph(
        "Le protocole compare la baseline vectorielle et l'agent hybride sur 8 questions. Les scores 0-5 couvrent "
        "la pertinence, l'exactitude, la traçabilité, le multi-hop et le score global."
    )
    add_image(doc, RESULTS / "fig_comparison.png", 6.4, "Figure 10 — Comparaison vectoriel vs hybride")
    add_table(
        doc,
        ["Question", "Difficulté", "Vectoriel", "Hybride", "Delta", "HITL"],
        [(row["id"], row["difficulty"], f"{row['vector']['score_global']:.2f}", f"{row['hybrid']['score_global']:.2f}", f"{row['delta']:+.2f}", row["hybrid_hitl"]) for row in COMPARISON["questions"]],
        widths=[2.0, 3.0, 2.5, 2.5, 2.0, 4.0],
        font_size=7.8,
    )
    add_table(
        doc,
        ["Métrique", "Vectoriel", "Hybride", "Delta"],
        [(metric, f"{COMPARISON['aggregates']['vector'][metric]:.2f}", f"{COMPARISON['aggregates']['hybrid'][metric]:.2f}", f"{COMPARISON['aggregates']['hybrid'][metric]-COMPARISON['aggregates']['vector'][metric]:+.2f}") for metric in ["pertinence", "exactitude", "tracabilite", "multi_hop", "score_global"]],
        widths=[5.0, 3.0, 3.0, 3.0],
    )

    # 13. Conclusion
    doc.add_heading("13. Conclusion", level=1)
    doc.add_paragraph(
        "QuantAgent démontre qu'un agent hybride peut répondre à des questions financières multi-hop de manière "
        "chiffrée, traçable et sécurisée. Sur le cas de référence, l'agent calcule une perte de -8,14 M€ pour un choc "
        "de +100 pb, soit -3,26 % de la NAV, identifie Vonovia, EDF, Enel, le Bund et AXA comme principaux contributeurs, "
        "constate le dépassement de la limite de 3,0 % et prépare un dossier HITL-RISK + HITL-IC."
    )
    add_table(
        doc,
        ["Critère de validation", "Résultat", "Preuve"],
        [
            ("JSON valide à 100 %", f"{VALIDATION['valid']}/{VALIDATION['total']}", "Schéma Draft 2020-12"),
            ("Agent hybride vecteur + graphe", f"{COMPARISON['aggregates']['hybrid']['score_global']:.2f}/5", f"{COMPARISON['aggregates']['graph_wins']}/{COMPARISON['aggregates']['questions']} questions"),
            ("Documentation sécurisée complète", "OK", "DOCX + PDF + Red Team"),
            ("Démo workflow + slides", "OK", "Dashboard 8007 + PPTX + n8n"),
        ],
        widths=[6.0, 4.0, 7.0],
    )
    doc.add_paragraph(
        "Les contributions principales sont : une architecture qui combine vectoriel, graphe et quantification ; "
        "un moteur de scénarios et de limites qui produit des chiffres auditables ; une couche de sécurité et un "
        "contrat JSON validé ; un workflow HITL qui empêche toute exécution automatique ; un dashboard, une API, "
        "un notebook et une documentation reproductibles."
    )
    doc.add_paragraph(
        "Le projet confirme également l'hypothèse de départ : la baseline vectorielle retrouve des passages pertinents "
        f"({COMPARISON['aggregates']['vector']['score_global']:.2f}/5) mais ne calcule pas, ne traverse pas le graphe et "
        f"ne déclenche pas HITL. L'agent hybride atteint {COMPARISON['aggregates']['hybrid']['score_global']:.2f}/5 et gagne "
        f"{COMPARISON['aggregates']['graph_wins']}/{COMPARISON['aggregates']['questions']} questions. La sécurité est "
        f"validée par {REDTEAM['blocked']}/{REDTEAM['total_attacks']} attaques bloquées et zéro faux positif."
    )
    doc.add_paragraph(
        "Les limites sont assumées : données synthétiques, moteur quantitatif simplifié, RAG TF-IDF, extraction par règles "
        "et HITL simulé. Les perspectives — embeddings denses, Neo4j, backtesting, alertes temps réel, audit réglementaire "
        "et signatures électroniques — sont détaillées dans la section 15. QuantAgent ne remplace pas l'humain : il lui "
        "prépare une décision traçable, chiffrée et contrôlée."
    )

    # 14. Reproductibilité
    doc.add_heading("14. Reproductibilité, Docker, n8n et GitHub", level=1)
    add_code(doc, "python -m venv .venv\n.venv\\Scripts\\activate\npip install -r requirements.txt\npython main.py demo\npython main.py serve\npython main.py api")
    doc.add_paragraph(
        "Docker expose le dashboard sur 8007 et l'API sur 8000. Le profil workflow ajoute n8n sur 5678. "
        "Le workflow n8n QuantAgent_n8n_FINAL.json appelle l'API, valide le contrat JSON, retourne 403 si la sécurité "
        "bloque, 202 si HITL est requis, 200 sinon."
    )
    add_code(doc, "docker compose up --build\ndocker compose --profile workflow up -d\n\n"
                  "POST http://localhost:5678/webhook/quantagent\n"
                  '{"question": "Quel est l\'impact d\'un choc de +100 pb sur les taux EUR ?"}')
    add_table(
        doc,
        ["Livrable", "Fichier"],
        [
            ("Dashboard", "app.py — port 8007"),
            ("API", "api.py — port 8000"),
            ("CLI", "main.py"),
            ("Notebook", "notebooks/QuantAgent_Agentic_AI_Quantitative_Finance.ipynb"),
            ("Workflow n8n", "workflows/QuantAgent_n8n_FINAL.json"),
            ("Docker", "Dockerfile + docker-compose.yml"),
            ("JSON final", "results/JSON_Final.json"),
            ("Documentation", "docs/Documentation_Agentic_AI_Quantitative_Finance.docx / .pdf"),
            ("Présentation", "docs/Presentation_Agentic_AI_Quantitative_Finance.pptx / .pdf"),
            ("GitHub", "github.com/kamalelafoui/agentic-ai-quantitative-finance"),
        ],
        widths=[4.5, 11.0],
    )

    # 15. Limites
    doc.add_heading("15. Limites et perspectives", level=1)
    add_bullets(doc, [
        "Données synthétiques : les chiffres sont cohérents mais ne représentent pas un portefeuille réel.",
        "Le moteur quantitatif est volontairement simple (chocs instantanés, sans convexité ni corrélations).",
        "Le RAG vectoriel est une baseline TF-IDF ; un embedding dense serait une extension naturelle.",
        "Le graphe est construit par règles ; une extraction LLM avec validation humaine pourrait enrichir le corpus.",
        "Le HITL est simulé dans le dashboard ; une intégration réelle nécessiterait un workflow de ticketing et des signatures.",
        "Perspectives : Neo4j, embeddings, backtesting, alertes temps réel, audit réglementaire, déploiement cloud.",
    ])

    # 16. Annexes
    doc.add_heading("16. Annexes", level=1)
    doc.add_heading("A. Contrat JSON (extrait)", level=2)
    add_code(doc, json.dumps({key: SHOWCASE[key] for key in ["request_id", "agent", "intent", "confidence", "hitl", "security", "meta"]}, ensure_ascii=False, indent=2)[:2200])
    doc.add_heading("B. Checklist de validation", level=2)
    add_table(
        doc,
        ["Critère", "Statut", "Preuve"],
        [
            ("JSON valide à 100 %", "OK", f"{VALIDATION['valid']}/{VALIDATION['total']}"),
            ("Agent hybride vecteur + graphe", "OK", "8/8 questions"),
            ("Documentation sécurisée complète", "OK", "DOCX + PDF + Red Team"),
            ("Démo workflow + slides", "OK", "Dashboard 8007 + PPTX"),
            ("HITL", "OK", "Risk / IC / Compliance / Model"),
            ("Docker + n8n + notebook + GitHub", "OK", "Livrables inclus"),
        ],
        widths=[6.0, 2.0, 8.0],
    )
    doc.add_heading("C. Avertissement", level=2)
    doc.add_paragraph(
        "QuantAgent est un outil de recherche et de démonstration pédagogique. Les données sont fictives. "
        "Les sorties ne constituent ni un conseil en investissement, ni une recommandation personnalisée, "
        "ni une exécution d'ordre. Toute décision reste soumise à validation humaine."
    )

    output = DOCS / "Documentation_Agentic_AI_Quantitative_Finance.docx"
    doc.save(output)
    print(output)


if __name__ == "__main__":
    main()

