"""API FastAPI de QuantAgent."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from quantagent.agent import QuantAgent
from quantagent.config import APP_NAME, APP_VERSION, GRAPH_PATH, REDTEAM_PATH, RESULTS_DIR, STATS_PATH
from quantagent.corpus import load_corpus, load_questions
from quantagent.hitl import PolicyEngine
from quantagent.knowledge_graph import KnowledgeGraph
from quantagent.quant import QuantEngine

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Agent hybride GraphRAG pour la finance quantitative — JSON, HITL et sécurité.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, examples=["Quel est l'impact d'un choc de +100 pb sur les taux ?"])
    portfolio_id: str = "PF-CORE-EU"
    scenario_id: str | None = None
    mode: Literal["hybrid", "vector", "graph"] = "hybrid"
    top_k: int = Field(default=4, ge=1, le=10)


class HitlRequest(BaseModel):
    request_id: str
    reviewer: str = "reviewer-demo"
    decision: Literal["APPROUVER", "REJETER", "ESCALADER"]
    comment: str = ""


@lru_cache(maxsize=1)
def get_agent() -> QuantAgent:
    documents = load_corpus()
    graph = KnowledgeGraph.from_files()
    return QuantAgent(documents, graph, quant=QuantEngine())


@app.get("/health")
def health():
    return {"status": "ok", "app": APP_NAME, "version": APP_VERSION}


@app.get("/stats")
def stats():
    if STATS_PATH.exists():
        return json.loads(STATS_PATH.read_text(encoding="utf-8"))
    graph = KnowledgeGraph.from_files()
    return {"graph": graph.stats(), "documents": len(load_corpus())}


@app.get("/questions")
def questions():
    return [question.to_dict() for question in load_questions()]


@app.get("/graph")
def graph_export():
    if GRAPH_PATH.exists():
        return json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    return {"nodes": [], "edges": []}


@app.get("/redteam")
def redteam():
    if REDTEAM_PATH.exists():
        return json.loads(REDTEAM_PATH.read_text(encoding="utf-8"))
    return {"attacks": [], "benign": []}


@app.post("/ask")
def ask(payload: AskRequest):
    try:
        result = get_agent().ask(
            payload.question,
            portfolio_id=payload.portfolio_id,
            scenario_id=payload.scenario_id,
            mode=payload.mode,
            top_k=payload.top_k,
        )
    except Exception as exc:  # pragma: no cover - réponse d'erreur API
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return result


@app.post("/hitl/decision")
def hitl_decision(payload: HitlRequest):
    try:
        record = PolicyEngine.log_decision(payload.request_id, payload.reviewer, payload.decision, payload.comment)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return record


@app.get("/")
def root():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "ask": "POST /ask",
        "results": str(RESULTS_DIR.name),
    }
