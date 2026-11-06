from __future__ import annotations

import json
from pathlib import Path

from quantagent.agent import QuantAgent
from quantagent.corpus import load_corpus, load_questions
from quantagent.knowledge_graph import KnowledgeGraph
from quantagent.quant import QuantEngine
from quantagent.schema import load_schema, validate_response


def test_schema_is_valid_json():
    schema = load_schema()
    assert schema["$schema"].startswith("https://json-schema.org/")


def test_showcase_json_valid():
    agent = QuantAgent(load_corpus(), KnowledgeGraph.from_files(), quant=QuantEngine())
    question = {item.id: item for item in load_questions()}["Q2"]
    result = agent.ask(question.question)
    assert validate_response(result) is True
    assert result["meta"]["json_valid"] is True


def test_showcase_file_valid():
    path = Path(__file__).resolve().parent.parent / "results" / "JSON_Final.json"
    if not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert validate_response(payload) is True
