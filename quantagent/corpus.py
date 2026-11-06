"""Chargement et normalisation des données de QuantAgent."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import (
    CORPUS_PATH,
    EDGES_PATH,
    NODES_PATH,
    PORTFOLIO_PATH,
    QUESTIONS_PATH,
    SCENARIOS_PATH,
)


def normalize(text: str) -> str:
    """Minuscule, sans accents, ponctuation réduite."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("’", "'").replace("–", "-").replace("—", "-")
    text = re.sub(r"[^a-z0-9%+\-.,' ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class Document:
    id: str
    title: str
    text: str
    type: str = ""
    date: str = ""
    department: str = ""
    classification: str = ""
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)

    @property
    def snippet(self) -> str:
        text = re.sub(r"\s+", " ", self.text).strip()
        return text[:280] + ("…" if len(text) > 280 else "")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "date": self.date,
            "department": self.department,
            "classification": self.classification,
            "summary": self.summary,
            "tags": self.tags,
            "entities": self.entities,
            "text": self.text,
        }


@dataclass
class Question:
    id: str
    question: str
    intent: str
    reference_answer: str
    expected_entities: list[str] = field(default_factory=list)
    expected_numbers: list[float] = field(default_factory=list)
    expected_docs: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    difficulty: str = "multi-hop"
    hops: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "intent": self.intent,
            "reference_answer": self.reference_answer,
            "expected_entities": self.expected_entities,
            "expected_numbers": self.expected_numbers,
            "expected_docs": self.expected_docs,
            "keywords": self.keywords,
            "difficulty": self.difficulty,
            "hops": self.hops,
        }


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_corpus(path: Path | None = None) -> list[Document]:
    rows = _read_json(path or CORPUS_PATH)
    return [
        Document(
            id=row["id"],
            title=row["title"],
            text=row["text"],
            type=row.get("type", ""),
            date=row.get("date", ""),
            department=row.get("department", ""),
            classification=row.get("classification", ""),
            summary=row.get("summary", ""),
            tags=row.get("tags", []),
            entities=row.get("entities", []),
        )
        for row in rows
    ]


def load_questions(path: Path | None = None) -> list[Question]:
    rows = _read_json(path or QUESTIONS_PATH)
    return [
        Question(
            id=row["id"],
            question=row["question"],
            intent=row.get("intent", "general"),
            reference_answer=row["reference_answer"],
            expected_entities=row.get("expected_entities", []),
            expected_numbers=row.get("expected_numbers", []),
            expected_docs=row.get("expected_docs", []),
            keywords=row.get("keywords", []),
            difficulty=row.get("difficulty", "multi-hop"),
            hops=row.get("hops", 1),
        )
        for row in rows
    ]


def load_portfolio(path: Path | None = None) -> dict[str, Any]:
    return _read_json(path or PORTFOLIO_PATH)


def load_scenarios(path: Path | None = None) -> list[dict[str, Any]]:
    return _read_json(path or SCENARIOS_PATH)


def load_nodes(path: Path | None = None) -> list[dict[str, Any]]:
    return _read_json(path or NODES_PATH)


def load_edges(path: Path | None = None) -> list[dict[str, Any]]:
    return _read_json(path or EDGES_PATH)
