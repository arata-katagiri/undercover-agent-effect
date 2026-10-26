import json
from types import SimpleNamespace

from collusion_discrete.adaptive_roles import (
    AgentMemory,
    LLMAdaptivePolicy,
    build_scenarios,
    parse_decision,
    run_matrix,
)
from collusion_discrete.analyze_adaptive import analyze


def test_matrix_includes_all_roles_and_39_cells():
    scenarios = build_scenarios()
    assert len(scenarios) == 39
    roles = {role for scenario in scenarios for role in scenario.roles}
    assert roles == {
        "adaptive", "loyalist", "opportunist", "double_agent", "whistleblower",
        "false_accuser", "bystander_auditor", "evidence_verifier", "counter_organizer",
        "netter", "provocateur",
    }


def test_nested_json_decision_updates_bounded_memory():
    memory = AgentMemory("observe", {"0": 0.5, "2": 0.5, "3": 0.5}, [], [])
    decision = parse_decision(
        '{"action":"TRANSFER","target":0,"strategy":"test trust","trust":{"0":1.7},'
        '"suspects":[2],"commitments":["temporary pact"],"stance":"accept",'
        '"report":{"suspect":2,"confidence":0.8}}',
        agent_id=1, valid_targets=[0, 2, 3], memory=memory,
    )
    assert decision.choice.target == 0
    assert decision.trust["0"] == 1.0
    assert decision.report == {"suspect": 2, "confidence": 0.8}


def test_deterministic_full_matrix_writes_outputs(tmp_path):
    rows = run_matrix(games_per_cell=1, base_seed=7, backend="deterministic",
                      workers=4, out_dir=str(tmp_path))
    assert len(rows) == 39
    assert all(row["pre_intervention_matched"] for row in rows)
    assert {row["family"] for row in rows} == {"betrayal", "reporting", "netter"}
    assert len(list((tmp_path / "game_record").glob("*.json"))) == 39
    metadata = json.loads((tmp_path / "experiment.json").read_text())
    assert metadata["scenario_cells"] == 39


def test_adaptive_analysis_reads_complete_matrix(tmp_path):
    output = tmp_path / "adaptive-analysis"
    run_matrix(games_per_cell=1, base_seed=7331, backend="deterministic",
               workers=4, out_dir=str(output))
    result = analyze(output)
    assert result["episodes"] == 39
    assert result["scenario_cells"] == 39
    assert result["all_pre_intervention_histories_matched"] is True
    assert result["total_public_fallbacks"] == 0
    assert set(result["netter_recruitment_compliance"]) == {"direct", "indirect", "none"}


def test_matched_conditions_clone_one_shared_prelude(tmp_path):
    rows = run_matrix(games_per_cell=1, base_seed=119, backend="deterministic",
                      workers=3, out_dir=str(tmp_path))
    grouped = {}
    for row in rows:
        grouped.setdefault(row["match_group"], []).append(row)
    for episodes in grouped.values():
        prehistories = {
            json.dumps(row["history"][:5], sort_keys=True)
            for row in episodes
        }
        assert len(prehistories) == 1


def test_three_illegal_outputs_fall_back_to_public():
    raw = ('{"action":"SABOTAGE","target":1,"strategy":"bad self target",'
           '"trust":{},"suspects":[],"commitments":[],"stance":"undecided",'
           '"report":null}')
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=raw))]
    )
    policy = LLMAdaptivePolicy.__new__(LLMAdaptivePolicy)
    policy.model = "fake"
    policy.repairs = []
    policy.client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_: response))
    )
    memory = AgentMemory("stay neutral", {"0": 0.5, "2": 0.5}, [], [])
    decision = policy.decide(
        agent_id=1, role="adaptive", round_number=4,
        scores={0: 0.0, 1: 0.0, 2: 0.0}, history=[], memory=memory,
        generation_seed=123,
    )
    assert decision.choice.action == "PUBLIC"
    assert decision.choice.target is None
    assert len(policy.repairs) == 3
    assert policy.repairs[-1]["fallback"] == "PUBLIC"
