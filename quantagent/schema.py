"""Validation du contrat JSON de QuantAgent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

from .config import SCHEMA_PATH


def load_schema(path: Path | None = None) -> dict[str, Any]:
    return json.loads((path or SCHEMA_PATH).read_text(encoding="utf-8"))


def validate_response(payload: dict[str, Any], schema: dict[str, Any] | None = None) -> bool:
    jsonschema.validate(instance=payload, schema=schema or load_schema())
    return True


def assert_valid(payload: dict[str, Any]) -> dict[str, Any]:
    validate_response(payload)
    return payload
