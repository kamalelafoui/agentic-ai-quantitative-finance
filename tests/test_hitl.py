from __future__ import annotations

from pathlib import Path

from quantagent.hitl import PolicyEngine


def test_hitl_requires_risk_for_breach():
    engine = PolicyEngine()
    quant = {"breaches": [{"control": "CTL-SCENARIO-LOSS"}], "impact_pct_nav": -3.26}
    result = engine.evaluate("scenario", quant, {"status": "allowed"}, "Quel est l'impact ?")
    assert result["required"] is True
    assert result["status"] == "PENDING_APPROVAL"
    assert result["approvals"][0]["id"] == "HITL-RISK"


def test_hitl_log_decision(tmp_path: Path):
    engine = PolicyEngine()
    log = tmp_path / "hitl.jsonl"
    record = engine.log_decision("REQ-TEST", "Risk Manager", "APPROUVER", "OK", path=log)
    assert record["decision"] == "APPROUVER"
    assert log.exists()
    assert "REQ-TEST" in log.read_text(encoding="utf-8")
