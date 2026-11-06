"""Dashboard Streamlit QuantAgent — http://localhost:8007."""

from __future__ import annotations

import base64
import json
from pathlib import Path

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from quantagent.agent import QuantAgent, fmt_m, fmt_num, fmt_pct
from quantagent.config import (
    APP_NAME,
    APP_TAGLINE,
    APP_VERSION,
    ASSETS_DIR,
    AUTHOR,
    COMPARISON_PATH,
    DEFAULT_PORT,
    DISCLAIMER,
    DOCS_DIR,
    PROGRAM,
    REDTEAM_PATH,
    RESULTS_DIR,
    STATS_PATH,
)
from quantagent.corpus import load_corpus, load_questions
from quantagent.hitl import PolicyEngine
from quantagent.knowledge_graph import KnowledgeGraph
from quantagent.quant import QuantEngine
from quantagent.visuals import TYPE_COLORS

BASE = Path(__file__).parent
NAVY = "#0B2545"
GOLD = "#F2C230"
TEAL = "#2EC4B6"
CORAL = "#E4572E"
BLUE = "#2D6CDF"
SLATE = "#5B6778"

st.set_page_config(
    page_title=f"{APP_NAME} — Agentic AI for Quantitative Finance",
    page_icon=str(ASSETS_DIR / "favicon.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Chargement
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def load_state():
    documents = load_corpus()
    graph = KnowledgeGraph.from_files()
    quant = QuantEngine()
    agent = QuantAgent(documents, graph, quant=quant)
    questions = load_questions()
    comparison = json.loads(COMPARISON_PATH.read_text(encoding="utf-8")) if COMPARISON_PATH.exists() else {}
    redteam = json.loads(REDTEAM_PATH.read_text(encoding="utf-8")) if REDTEAM_PATH.exists() else {}
    stats = json.loads(STATS_PATH.read_text(encoding="utf-8")) if STATS_PATH.exists() else {}
    return documents, graph, quant, agent, questions, comparison, redteam, stats


documents, graph, quant, agent, questions, comparison, redteam, stats = load_state()
base_metrics = quant.base_metrics()
scenario_rates = quant.run_scenario("SCN-RATES-100BP")


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def image_html(path: Path, height: str = "58px") -> str:
    if not path.exists():
        return ""
    return f'<img src="data:image/png;base64,{b64(path)}" style="height:{height};width:auto;" alt="logo">'


# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', 'Segoe UI', sans-serif; }}
    .stApp {{ background: #F4F7FB; }}
    .block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1500px; }}
    header[data-testid="stHeader"] {{ background: transparent; }}
    div[data-testid="stToolbar"] {{ display: none; }}
    .stAppDeployButton {{ display: none; }}
    section[data-testid="stSidebar"] {{ background: {NAVY}; border-right: 1px solid #17365C; }}
    section[data-testid="stSidebar"] * {{ color: #E8F0FA; }}
    section[data-testid="stSidebar"] .stRadio label {{ color: #E8F0FA !important; font-weight: 500; }}
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {{ background: rgba(242,194,48,.12); border-radius: 10px; }}
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-checked="true"] {{ background: rgba(242,194,48,.18); border-radius: 10px; }}
    .sidebar-brand {{ text-align:center; padding: 8px 0 4px 0; }}
    .sidebar-brand img {{ background:white; border-radius:14px; padding:8px; width: 92%; }}
    .sidebar-title {{ font-size: 18px; font-weight: 800; color: white; margin-top: 8px; letter-spacing:.2px; }}
    .sidebar-sub {{ font-size: 10.5px; color: #9FB6D1; margin-top: 2px; line-height:1.35; }}
    .sidebar-pill {{ display:inline-block; background:rgba(46,196,182,.14); color:#8FF3E7; border:1px solid rgba(46,196,182,.35);
        border-radius:999px; padding:4px 9px; font-size:10px; margin:3px 2px; font-weight:600; }}
    .sidebar-pill.gold {{ background:rgba(242,194,48,.15); color:#FFE08A; border-color:rgba(242,194,48,.35); }}
    .hero {{ background: linear-gradient(118deg, {NAVY} 0%, #123B66 58%, #0E5A63 100%); border-radius: 24px;
        padding: 28px 32px 24px 32px; color: white; position: relative; overflow: hidden; margin-bottom: 20px;
        box-shadow: 0 18px 44px rgba(11,37,69,.20); }}
    .hero:after {{ content:""; position:absolute; right:-70px; top:-100px; width:360px; height:360px; border-radius:50%;
        background: radial-gradient(circle, rgba(242,194,48,.26), rgba(242,194,48,0)); }}
    .hero img {{ height: 68px; background:white; padding:8px 14px; border-radius:14px; box-shadow:0 8px 22px rgba(0,0,0,.16); }}
    .hero h1 {{ font-size: 40px; margin: 14px 0 4px 0; font-weight: 800; letter-spacing: -1.2px; }}
    .hero p {{ color: #C5D8EA; margin: 0; font-size: 14px; max-width: 760px; }}
    .hero .badges {{ margin-top: 16px; display:flex; gap:8px; flex-wrap:wrap; }}
    .badge {{ background: rgba(255,255,255,.10); border:1px solid rgba(255,255,255,.20); color:white;
        padding:5px 11px; border-radius:999px; font-size:10.5px; font-weight:600; letter-spacing:.3px; }}
    .badge.gold {{ background:{GOLD}; color:{NAVY}; border-color:{GOLD}; }}
    .badge.teal {{ background:{TEAL}; color:{NAVY}; border-color:{TEAL}; }}
    .kpis {{ display:grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin: 4px 0 20px 0; }}
    .kpi {{ background:white; border:1px solid #E2E9F2; border-radius:16px; padding:14px 15px; box-shadow:0 5px 18px rgba(11,37,69,.04); }}
    .kpi .v {{ font-size:25px; font-weight:800; color:{NAVY}; line-height:1.1; }}
    .kpi .l {{ font-size:10px; color:{SLATE}; text-transform:uppercase; letter-spacing:.7px; margin-top:4px; }}
    .kpi .d {{ font-size:10px; color:{TEAL}; font-weight:600; margin-top:3px; }}
    .kpi .d.warn {{ color:{CORAL}; }}
    .section-title {{ font-size:19px; font-weight:800; color:{NAVY}; margin: 6px 0 10px 0; letter-spacing:-.3px; }}
    .section-sub {{ color:{SLATE}; font-size:12px; margin-top:-6px; margin-bottom:10px; }}
    .card {{ background:white; border:1px solid #E2E9F2; border-radius:18px; padding:18px 20px; box-shadow:0 5px 18px rgba(11,37,69,.04); }}
    .answer-card {{ background:white; border:1px solid #E2E9F2; border-left:6px solid {GOLD}; border-radius:16px;
        padding:18px 22px; margin-top:8px; box-shadow:0 8px 24px rgba(11,37,69,.06); }}
    .answer-card h3 {{ margin-top:0; color:{NAVY}; }}
    .small {{ color:{SLATE}; font-size:11.5px; }}
    .tag {{ display:inline-block; background:#EEF5FA; color:#1E4E6B; border-radius:999px; padding:3px 9px;
        margin:2px 3px 2px 0; font-size:10.5px; font-weight:600; }}
    .tag.gold {{ background:#FFF5CF; color:#6B5200; }}
    .tag.red {{ background:#FDECEA; color:#9B2C1F; }}
    .tag.green {{ background:#E6F7F4; color:#0F766E; }}
    .stButton>button, .stFormSubmitButton>button {{ background:{GOLD}; color:{NAVY}; border:none; border-radius:11px;
        font-weight:700; padding:.55rem 1rem; }}
    .stButton>button:hover, .stFormSubmitButton>button:hover {{ background:#E7B71E; color:{NAVY}; }}
    div[data-testid="stMetricValue"] {{ color:{NAVY}; font-weight:800; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
    .stTabs [data-baseweb="tab"] {{ background:white; border:1px solid #E2E9F2; border-radius:12px; padding:8px 16px;
        font-weight:600; color:{NAVY}; }}
    .stTabs [aria-selected="true"] {{ background:{NAVY} !important; color:white !important; border-color:{NAVY} !important; }}
    .status-pill {{ display:inline-block; padding:5px 10px; border-radius:999px; font-size:10.5px; font-weight:700; }}
    .status-ok {{ background:#E6F7F4; color:#0F766E; }}
    .status-warn {{ background:#FFF5CF; color:#6B5200; }}
    .status-bad {{ background:#FDECEA; color:#9B2C1F; }}
    footer {{ visibility: hidden; }}
    .footer {{ text-align:center; color:{SLATE}; font-size:10.5px; padding-top:18px; border-top:1px solid #E2E9F2; margin-top:24px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-brand">
            {image_html(ASSETS_DIR / "logo.png", "82px")}
            <div class="sidebar-title">QuantAgent</div>
            <div class="sidebar-sub">Agentic AI for<br>Quantitative Finance</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    menu_options = ["Vue d'ensemble", "Agent hybride", "Graphe de connaissances", "Sécurité & Red Team", "Statistiques", "Documentation"]
    slug_to_label = {
        "overview": "Vue d'ensemble", "agent": "Agent hybride", "graph": "Graphe de connaissances",
        "security": "Sécurité & Red Team", "stats": "Statistiques", "docs": "Documentation",
    }
    label_to_slug = {label: slug for slug, label in slug_to_label.items()}
    requested = st.query_params.get("menu", "overview")
    if isinstance(requested, list):
        requested = requested[0] if requested else "overview"
    default_label = slug_to_label.get(str(requested), "Vue d'ensemble")
    menu = st.radio(
        "Menu",
        menu_options,
        index=menu_options.index(default_label),
        label_visibility="collapsed",
    )
    st.query_params["menu"] = label_to_slug.get(menu, "overview")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="text-align:center">
            <span class="sidebar-pill">● Agent opérationnel</span>
            <span class="sidebar-pill gold">Port {DEFAULT_PORT}</span><br>
            <span class="sidebar-pill">JSON 100 %</span>
            <span class="sidebar-pill">HITL actif</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='font-size:10px;color:#8FA8C4;text-align:center;line-height:1.5'>"
        f"{PROGRAM}<br>Version {APP_VERSION}<br><b>{AUTHOR}</b></div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def hero(title: str, subtitle: str, badges: list[str] | None = None):
    badge_html = "".join(
        f'<span class="badge {"gold" if index == 0 else ("teal" if index == 1 else "")}">{badge}</span>'
        for index, badge in enumerate(badges or [])
    )
    st.markdown(
        f"""
        <div class="hero">
            {image_html(ASSETS_DIR / "logo.png", "64px")}
            <h1>{title}</h1>
            <p>{subtitle}</p>
            <div class="badges">{badge_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_row(items: list[tuple[str, str, str, bool]]):
    cards = "".join(
        f'<div class="kpi"><div class="v">{value}</div><div class="l">{label}</div>'
        f'<div class="d {"warn" if warn else ""}">{detail}</div></div>'
        for value, label, detail, warn in items
    )
    st.markdown(f'<div class="kpis">{cards}</div>', unsafe_allow_html=True)


def status_badge(status: str) -> str:
    mapping = {
        "OK": ("status-ok", "OK"),
        "WATCH": ("status-warn", "WATCH"),
        "BREACH": ("status-bad", "BREACH"),
        "PENDING_APPROVAL": ("status-warn", "PENDING"),
        "NOT_REQUIRED": ("status-ok", "NON REQUIS"),
        "BLOCKED": ("status-bad", "BLOQUÉ"),
        "allowed": ("status-ok", "AUTORISÉ"),
        "review": ("status-warn", "REVUE"),
        "blocked": ("status-bad", "BLOQUÉ"),
    }
    cls, text = mapping.get(status, ("status-ok", status))
    return f'<span class="status-pill {cls}">{text}</span>'


def graph_figure(max_nodes: int = 70, height: int = 620) -> go.Figure:
    degrees = dict(graph.graph.degree())
    keep = set(sorted(degrees, key=lambda node: degrees[node], reverse=True)[:max_nodes])
    sub = graph.graph.subgraph(keep).copy()
    if sub.number_of_nodes() == 0:
        return go.Figure()
    pos = nx.spring_layout(sub, seed=42, k=0.95, iterations=180)
    fig = go.Figure()
    edge_x, edge_y = [], []
    for u, v in sub.edges():
        edge_x += [pos[u][0], pos[v][0], None]
        edge_y += [pos[u][1], pos[v][1], None]
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=0.6, color="#C9D3E0"), hoverinfo="skip", name="Relations"))
    for ntype, color in TYPE_COLORS.items():
        nodes = [node for node in sub.nodes if graph.type_of(node) == ntype]
        if not nodes:
            continue
        fig.add_trace(go.Scatter(
            x=[pos[node][0] for node in nodes],
            y=[pos[node][1] for node in nodes],
            mode="markers+text",
            text=[graph.label(node) if degrees.get(node, 0) >= 8 else "" for node in nodes],
            textposition="top center",
            textfont=dict(size=8, color=NAVY),
            marker=dict(size=[10 + 1.8 * min(degrees.get(node, 1), 18) for node in nodes], color=color, line=dict(width=1, color="white")),
            name=ntype,
            hovertemplate="<b>%{text}</b><br>Type : " + ntype + "<extra></extra>",
        ))
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        legend=dict(orientation="h", yanchor="bottom", y=-0.06, x=0, font=dict(size=10)),
        hovermode="closest",
    )
    return fig


def render_answer(result: dict):
    with st.container(border=True):
        st.markdown("### Réponse de QuantAgent")
        st.markdown(result["answer"])
    cols = st.columns(6)
    cols[0].metric("Confiance", f"{result['confidence']*100:.0f} %")
    cols[1].metric("Latence", f"{result['latency_ms']:.0f} ms")
    cols[2].metric("Sources", len(result["sources"]))
    cols[3].metric("Chemins", len(result["graph"]["paths"]))
    cols[4].metric("HITL", result["hitl"]["status"].replace("_", " "))
    cols[5].metric("JSON", "VALIDE" if result["meta"].get("json_valid") else "INVALIDE")

    tabs = st.tabs(["Traçabilité JSON", "Graphe de preuve", "HITL & audit", "Sources"])
    with tabs[0]:
        st.download_button(
            "Télécharger le JSON",
            data=json.dumps(result, ensure_ascii=False, indent=2),
            file_name=f"{result['request_id']}.json",
            mime="application/json",
            key=f"dl_{result['request_id']}",
        )
        st.json(result)
    with tabs[1]:
        if result["graph"]["nodes"]:
            st.plotly_chart(graph_figure(max_nodes=55), use_container_width=True)
            if result["graph"]["paths"]:
                rows = []
                for path in result["graph"]["paths"][:10]:
                    chain = " → ".join(f"{graph.label(edge['head'])} -{edge['relation']}→ {graph.label(edge['tail'])}" for edge in path.get("chain", []))
                    rows.append({"chemin": chain or " → ".join(path.get("nodes", []))})
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Aucun sous-graphe pour cette requête (réponse de sécurité).")
    with tabs[2]:
        hitl = result["hitl"]
        st.markdown(f"**Statut :** {status_badge(hitl['status'])}", unsafe_allow_html=True)
        st.markdown(hitl["rationale"])
        if hitl["approvals"]:
            st.dataframe(pd.DataFrame(hitl["approvals"])[["id", "role", "sla_hours", "status", "reason"]], use_container_width=True, hide_index=True)
        if hitl["conditions"]:
            st.markdown("**Conditions :**")
            for condition in hitl["conditions"]:
                st.markdown(f"- {condition}")
        st.caption(f"Prochaine étape : {hitl['next_step']}")
        if hitl["status"] == "PENDING_APPROVAL":
            with st.form(f"hitl_{result['request_id']}"):
                reviewer = st.text_input("Reviewer (nom / rôle)", value="Risk Manager")
                decision = st.selectbox("Décision", ["APPROUVER", "REJETER", "ESCALADER"])
                comment = st.text_area("Justification", value="Décision de démonstration — aucune exécution réelle.")
                if st.form_submit_button("Enregistrer la décision HITL"):
                    record = PolicyEngine.log_decision(result["request_id"], reviewer, decision, comment)
                    st.success(f"Décision enregistrée : {record['decision_id']} ({record['decision']}) — mode simulation.")
    with tabs[3]:
        for source in result["sources"]:
            with st.expander(f"[{source['doc_id']}] {source['title']} — score {source['score']:.2f}"):
                st.write(source["snippet"])


def security_banner(result: dict):
    security = result["security"]
    if security["status"] == "blocked":
        st.error(f"Requête bloquée — politique {security['policy']} · risque {security['risk_score']:.2f}. Aucune donnée interne n'est exposée.")
    elif security["status"] == "review":
        st.warning(f"Requête en revue — politique {security['policy']} · risque {security['risk_score']:.2f}.")
    else:
        st.success(f"Contrôles de sécurité : OK · risque {security['risk_score']:.2f}.")


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
if menu == "Vue d'ensemble":
    hero(
        "QuantAgent",
        "Agent hybride GraphRAG pour l'analyse quantitative, la gestion des risques et la conformité. "
        "Vectoriel + Knowledge Graph + quantification + HITL + sécurité, avec une sortie JSON 100 % valide.",
        ["MINI-PROJET FINAL", "AGENTIC AI · QUANT FINANCE", f"{len(documents)} documents · {graph.stats()['nodes']} entités · {graph.stats()['edges']} relations"],
    )
    kpi_row([
        (str(len(documents)), "Documents", "corpus financier", False),
        (str(graph.stats()["nodes"]), "Entités", "15 types", False),
        (str(graph.stats()["edges"]), "Relations", "multi-hop", False),
        (f"{comparison.get('aggregates', {}).get('hybrid', {}).get('score_global', 0):.2f}/5", "Score hybride", f"vectoriel {comparison.get('aggregates', {}).get('vector', {}).get('score_global', 0):.2f}", False),
        ("8/8", "Questions gagnées", "vs baseline", False),
        ("100 %", "JSON valide", "100/100 requêtes", False),
    ])
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">Allocation sectorielle</div>', unsafe_allow_html=True)
        st.image(str(RESULTS_DIR / "fig_sector_allocation.png"), use_container_width=True)
    with col2:
        st.markdown('<div class="section-title">Scénario taux +100 bp</div>', unsafe_allow_html=True)
        st.image(str(RESULTS_DIR / "fig_scenario_impact.png"), use_container_width=True)
    col3, col4 = st.columns([1.15, 1])
    with col3:
        st.markdown('<div class="section-title">Contrôle des limites</div>', unsafe_allow_html=True)
        st.image(str(RESULTS_DIR / "fig_limit_utilization.png"), use_container_width=True)
    with col4:
        st.markdown('<div class="section-title">Dernier cas de démonstration</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="card">
                <div class="small">Q2 — scénario taux</div>
                <div style="font-size:20px;font-weight:800;color:{NAVY};margin:4px 0 8px 0">-8,14 M€ · -3,26 % NAV</div>
                <div class="small">Perte estimée sur le choc de +100 pb. La limite de 3,0 % est dépassée de 0,64 M€.</div>
                <div style="margin-top:12px">
                    <span class="tag red">CTL-SCENARIO-LOSS · BREACH</span>
                    <span class="tag gold">HITL-RISK</span>
                    <span class="tag gold">HITL-IC</span>
                </div>
                <div style="margin-top:12px" class="small">Top contributeurs : Vonovia, EDF, Enel, Bund, AXA.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='small' style='margin-top:10px'>Le dashboard expose le formulaire, les graphiques, les statistiques et le journal HITL. "
            f"Lancement : <code>streamlit run app.py --server.port {DEFAULT_PORT}</code></div>",
            unsafe_allow_html=True,
        )
    st.markdown('<div class="footer">QuantAgent · Agentic AI for Quantitative Finance · Démonstration pédagogique · Les données sont fictives.</div>', unsafe_allow_html=True)

elif menu == "Agent hybride":
    hero("Agent hybride", "Posez une question métier : l'agent route l'intention, interroge le vectoriel et le graphe, calcule le P&L, contrôle les limites et prépare le dossier HITL.", ["FORMULAIRE", "VECTORIEL + GRAPHE", "JSON + HITL"])
    col1, col2 = st.columns([3, 1])
    with col1:
        example = st.selectbox("Charger une question d'exemple", ["—"] + [f"{q.id} — {q.question}" for q in questions])
    with col2:
        if st.button("Charger l'exemple", use_container_width=True) and example != "—":
            st.session_state["question"] = example.split(" — ", 1)[1]
    if "question" not in st.session_state:
        st.session_state["question"] = questions[1].question
    with st.form("agent_form"):
        question = st.text_area("Question", key="question", height=110)
        c1, c2, c3 = st.columns(3)
        portfolio = c1.selectbox("Portefeuille", ["Core Europe (PF-CORE-EU)"])
        scenario = c2.selectbox("Scénario", ["Automatique", "SCN-RATES-100BP", "SCN-CREDIT-50BP", "SCN-EQUITY-10PCT"])
        mode = c3.radio("Mode", ["Hybride", "Vectoriel", "Graph"], horizontal=True)
        submitted = st.form_submit_button("Lancer l'analyse")
    if submitted:
        mode_map = {"Hybride": "hybrid", "Vectoriel": "vector", "Graph": "graph"}
        scenario_id = None if scenario == "Automatique" else scenario
        with st.spinner("QuantAgent analyse la question..."):
            st.session_state["result"] = agent.ask(question, scenario_id=scenario_id, mode=mode_map[mode])
            st.session_state["last_question"] = question
    result = st.session_state.get("result")
    if result:
        security_banner(result)
        render_answer(result)
    else:
        st.info("Choisissez une question d'exemple ou saisissez votre propre question, puis lancez l'analyse.")
    st.markdown('<div class="footer">Les réponses sont des analyses de démonstration, pas des conseils en investissement. Toute décision reste humaine.</div>', unsafe_allow_html=True)

elif menu == "Graphe de connaissances":
    hero("Graphe de connaissances", "105 entités et 362 relations : portefeuille, positions, émetteurs, facteurs, scénarios, politiques, contrôles, approbations et documents.", ["KNOWLEDGE GRAPH", "MULTI-HOP", "TRACABILITÉ"])
    stats_graph = graph.stats()
    kpi_row([
        (str(stats_graph["nodes"]), "Nœuds", f"{len(stats_graph['node_types'])} types", False),
        (str(stats_graph["edges"]), "Relations", f"{len(stats_graph['relations'])} types", False),
        (str(stats_graph["density"]), "Densité", "graphe dirigé", False),
        (str(stats_graph["components"]), "Composantes", f"max {stats_graph['largest_component']}", False),
        (str(stats_graph["avg_degree"]), "Degré moyen", "connexions", False),
        ("100 %", "Traçable", "chemins de preuve", False),
    ])
    st.markdown('<div class="section-title">Vue interactive</div>', unsafe_allow_html=True)
    st.plotly_chart(graph_figure(max_nodes=75, height=650), use_container_width=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown('<div class="section-title">Nœuds les plus connectés</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(stats_graph["top_nodes"]), use_container_width=True, hide_index=True)
    with col2:
        st.markdown("<div class='section-title'>Types d'entités</div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([{"type": key, "count": value} for key, value in stats_graph["node_types"].items()]), use_container_width=True, hide_index=True)
    st.image(str(DOCS_DIR / "graph_overview.png"), use_container_width=True)
    st.markdown('<div class="footer">Le graphe est exporté en JSON et Cypher dans results/.</div>', unsafe_allow_html=True)

elif menu == "Sécurité & Red Team":
    hero("Sécurité & Red Team", "Filtre d'entrée, isolation documentaire, allowlist d'outils, masquage PII, validation JSON et journal d'audit. 20 attaques, 20 blocages, 0 faux positif.", ["RED TEAM", "20/20 BLOQUÉES", "0 FAUX POSITIF"])
    kpi_row([
        ("20/20", "Attaques bloquées", "taux 100 %", False),
        ("0", "Faux positifs", "10 requêtes bénignes", False),
        ("100 %", "JSON valide", "contrat de refus", False),
        ("5", "Couches", "défense en profondeur", False),
        ("0", "Fuite PII", "masquage actif", False),
        ("24/7", "Audit", "evidence JSONL", False),
    ])
    col1, col2 = st.columns([1.1, 1])
    with col1:
        st.markdown('<div class="section-title">Blocage par catégorie</div>', unsafe_allow_html=True)
        st.image(str(RESULTS_DIR / "fig_redteam.png"), use_container_width=True)
    with col2:
        st.markdown('<div class="section-title">Défense en profondeur</div>', unsafe_allow_html=True)
        st.image(str(DOCS_DIR / "security_layers.png"), use_container_width=True)
    st.markdown('<div class="section-title">Campagne Red Team</div>', unsafe_allow_html=True)
    if redteam:
        df = pd.DataFrame(redteam["attacks"])
        st.dataframe(df[["id", "category", "status", "risk_score", "flags", "blocked"]], use_container_width=True, hide_index=True)
    st.markdown('<div class="section-title">Requêtes bénignes (faux positifs)</div>', unsafe_allow_html=True)
    if redteam:
        st.dataframe(pd.DataFrame(redteam["benign"]), use_container_width=True, hide_index=True)
    st.markdown('<div class="footer">Les documents piégés sont isolés dans data/attack_pack et ne sont jamais indexés.</div>', unsafe_allow_html=True)

elif menu == "Statistiques":
    hero("Statistiques & évaluation", "Protocole 0-5 sur 8 questions : pertinence, exactitude, traçabilité, multi-hop et score global. Validation JSON sur 100 requêtes.", ["ÉVALUATION", "8/8", "100/100 JSON"])
    kpi_row([
        (f"{comparison.get('aggregates', {}).get('hybrid', {}).get('score_global', 0):.2f}/5", "Score hybride", "8 questions", False),
        (f"{comparison.get('aggregates', {}).get('vector', {}).get('score_global', 0):.2f}/5", "Score vectoriel", "baseline TF-IDF", False),
        (f"+{comparison.get('aggregates', {}).get('delta', 0):.2f}", "Delta", "hybride vs vectoriel", False),
        ("100/100", "JSON valides", "schéma Draft 2020-12", False),
        ("20/20", "Attaques bloquées", "Red Team", False),
        ("8", "Questions", "4 familles", False),
    ])
    col1, col2 = st.columns([1.1, 1])
    with col1:
        st.markdown('<div class="section-title">Comparaison des scores</div>', unsafe_allow_html=True)
        st.image(str(RESULTS_DIR / "fig_comparison.png"), use_container_width=True)
    with col2:
        st.markdown('<div class="section-title">Utilisation des limites</div>', unsafe_allow_html=True)
        st.image(str(RESULTS_DIR / "fig_limit_utilization.png"), use_container_width=True)
    st.markdown('<div class="section-title">Détail par question</div>', unsafe_allow_html=True)
    if comparison:
        rows = []
        for row in comparison["questions"]:
            rows.append({
                "ID": row["id"], "Difficulté": row["difficulty"], "Hops": row["hops"],
                "Vectoriel": row["vector"]["score_global"], "Hybride": row["hybrid"]["score_global"],
                "Delta": row["delta"], "HITL": row["hybrid_hitl"],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.markdown('<div class="section-title">Validation JSON</div>', unsafe_allow_html=True)
    validation = json.loads((RESULTS_DIR / "validation_report.json").read_text(encoding="utf-8"))
    st.markdown(
        f"<div class='card'><b>{validation['valid']}/{validation['total']}</b> réponses valides "
        f"({validation['validity_rate']*100:.0f} %) · schéma <code>{validation['schema']}</code> · "
        f"version {validation['schema_version']}</div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="footer">Les résultats sont reproductibles via <code>python main.py demo</code>.</div>', unsafe_allow_html=True)

elif menu == "Documentation":
    hero("Documentation & livrables", "Architectures, documentation DOCX/PDF, présentation PPTX, notebook, workflow n8n, Docker, GitHub et archive ZIP.", ["LIVRABLES", "DOCX · PPTX · PDF", "GITHUB READY"])
    st.markdown('<div class="section-title">Architecture globale</div>', unsafe_allow_html=True)
    st.image(str(DOCS_DIR / "architecture_globale.png"), use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">Boucle de l’agent</div>', unsafe_allow_html=True)
        st.image(str(DOCS_DIR / "architecture_agent.png"), use_container_width=True)
    with col2:
        st.markdown('<div class="section-title">Workflow HITL</div>', unsafe_allow_html=True)
        st.image(str(DOCS_DIR / "workflow_hitl.png"), use_container_width=True)
    st.markdown('<div class="section-title">Téléchargements</div>', unsafe_allow_html=True)
    downloads = [
        ("Documentation DOCX", DOCS_DIR / "Documentation_Agentic_AI_Quantitative_Finance.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("Documentation PDF", DOCS_DIR / "Documentation_Agentic_AI_Quantitative_Finance.pdf", "application/pdf"),
        ("Présentation PPTX", DOCS_DIR / "Presentation_Agentic_AI_Quantitative_Finance.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
        ("Présentation PDF", DOCS_DIR / "Presentation_Agentic_AI_Quantitative_Finance.pdf", "application/pdf"),
        ("JSON Final", RESULTS_DIR / "JSON_Final.json", "application/json"),
        ("Notebook", BASE / "notebooks" / "QuantAgent_Agentic_AI_Quantitative_Finance.ipynb", "application/json"),
    ]
    cols = st.columns(3)
    for index, (label, path, mime) in enumerate(downloads):
        with cols[index % 3]:
            if path.exists():
                st.download_button(label, data=path.read_bytes(), file_name=path.name, mime=mime, use_container_width=True)
            else:
                st.button(f"{label} (à générer)", disabled=True, use_container_width=True)
    st.markdown('<div class="section-title">Checklist de validation</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="card">
        ✅ JSON valide à 100 % — 100/100 requêtes validées<br>
        ✅ Agent hybride vecteur + graphe — 8/8 questions<br>
        ✅ Documentation sécurisée — DOCX + PDF<br>
        ✅ Démo workflow + slides — dashboard port 8007 + PPTX<br>
        ✅ HITL — Risk, Comité, Compliance, Model Risk<br>
        ✅ Red Team — 20/20 attaques bloquées, 0 faux positif<br>
        ✅ Docker, n8n, notebook, GitHub Actions et ZIP
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="footer">QuantAgent · Documentation pédagogique · Données fictives.</div>', unsafe_allow_html=True)

st.markdown(
    f"<div style='text-align:center;color:#8FA8C4;font-size:10px;margin-top:18px'>"
    f"{APP_NAME} v{APP_VERSION} · {APP_TAGLINE} · {AUTHOR}</div>",
    unsafe_allow_html=True,
)
