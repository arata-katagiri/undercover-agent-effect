import pytest

from collusion_discrete.verify_run import _audit_adaptive_raw_decisions, _audit_csv_rows


def test_csv_audit_requires_exact_raw_values():
    records = [{"condition": "control", "seed": 7, "replicate": 1,
                "score": 2.5, "accepted": None}]
    rows = [{"condition": "control", "seed": "7", "replicate": "1",
             "score": "2.5", "accepted": ""}]
    _audit_csv_rows(rows, records, "confirmatory")
    rows[0]["score"] = "99.0"
    with pytest.raises(AssertionError, match="CSV/raw mismatch"):
        _audit_csv_rows(rows, records, "confirmatory")


def test_adaptive_raw_action_must_equal_scored_action():
    record = {
        "roles": ["provocateur", "adaptive", "adaptive", "adaptive"],
        "history": [{"choices": {"1": {"action": "TRANSFER", "target": 0}}}],
        "decision_log": [{"round": 1, "agent": 1,
                          "raw": '{"action":"TRANSFER","target":0}'}],
        "action_repair_events": [],
    }
    assert _audit_adaptive_raw_decisions(record) == 1
    record["history"][0]["choices"]["1"] = {"action": "KEEP", "target": None}
    with pytest.raises(AssertionError, match="raw/scored action mismatch"):
        _audit_adaptive_raw_decisions(record)


def test_adaptive_invalid_raw_requires_logged_public_fallback():
    record = {
        "roles": ["provocateur", "adaptive", "adaptive", "adaptive"],
        "history": [{"choices": {"1": {"action": "PUBLIC", "target": None}}}],
        "decision_log": [{"round": 1, "agent": 1,
                          "raw": '{"action":"SABOTAGE","target":1}'}],
        "action_repair_events": [{"round": 1, "agent_id": 1, "fallback": "PUBLIC"}],
    }
    assert _audit_adaptive_raw_decisions(record) == 1
