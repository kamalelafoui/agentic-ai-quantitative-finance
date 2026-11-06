from __future__ import annotations

import pytest

from quantagent.agent import QuantAgent
from quantagent.corpus import load_corpus, load_questions
from quantagent.knowledge_graph import KnowledgeGraph
from quantagent.quant import QuantEngine
from quantagent.schema import validate_response


@pytest.fixture(scope="module")
def agent() -> QuantAgent:
    return QuantAgent(load_corpus(), KnowledgeGraph.from_files(), quant=QuantEngine())


@pytest.fixture(scope="module")
def questions():
    return {question.id: question for question in load_questions()}


def test_scenario_impact_and_hitl(agent, questions):
    result = agent.ask(questions["Q2"].question)
    assert result["intent"] == "scenario"
    assert result["quant"]["impact_eur"] == pytest.approx(-8_140_400, abs=1)
    assert result["quant"]["impact_pct_nav"] == pytest.approx(-3.256, abs=0.01)
    assert result["hitl"]["status"] == "PENDING_APPROVAL"
    assert result["meta"]["json_valid"] is True
    assert "D21" in {source["doc_id"] for source in result["sources"]}
    assert result["graph"]["paths"]


def test_limits_breach(agent, questions):
    result = agent.ask(questions["Q3"].question)
    assert result["intent"] == "limits"
    checks = {check["control"]: check for check in result["quant"]["limit_checks"]}
    assert checks["CTL-SCENARIO-LOSS"]["status"] == "BREACH"
    assert checks["CTL-ISSUER-CAP"]["status"] == "OK"
    assert "HITL-RISK" in result["answer"]


def test_approval_circuit(agent, questions):
    result = agent.ask(questions["Q4"].question)
    assert result["intent"] == "approval"
    approvals = {item["id"] for item in result["hitl"]["approvals"]}
    assert {"HITL-RISK", "HITL-IC"}.issubset(approvals)
    assert "19,5" in result["answer"]


def test_esg_intersection(agent, questions):
    result = agent.ask(questions["Q5"].question)
    assert result["intent"] == "esg"
    assert "Vonovia" in result["answer"]
    assert "EDF" in result["answer"]
    assert "HITL-COMPLIANCE" in result["answer"]


def test_data_policy_blocks_pii(agent, questions):
    result = agent.ask(questions["Q7"].question)
    assert result["intent"] == "data_policy"
    assert result["security"]["status"] == "blocked"
    assert result["hitl"]["status"] == "PENDING_APPROVAL"
    assert "D17" in {source["doc_id"] for source in result["sources"]}


def test_prompt_injection_blocked(agent, questions):
    result = agent.ask(questions["Q8"].question)
    assert result["intent"] == "security"
    assert result["security"]["status"] == "blocked"
    assert result["hitl"]["status"] == "BLOCKED"
    assert "bloquée" in result["answer"].lower()


def test_vector_baseline_is_valid_json(agent, questions):
    result = agent.ask(questions["Q2"].question, mode="vector", evaluation_baseline=True)
    assert validate_response(result) is True
    assert result["quant"] is None
    assert result["graph"]["paths"] == []
