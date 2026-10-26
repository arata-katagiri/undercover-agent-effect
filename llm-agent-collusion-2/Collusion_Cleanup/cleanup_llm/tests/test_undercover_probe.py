"""Focused tests for the undercover-probe experiment instrumentation."""

from cleanup_llm.agents.llm_agent import LLMAgent
from cleanup_llm.cleanup.config import CleanupConfig
from cleanup_llm.cleanup.env import CleanupEnvironment
from cleanup_llm.games.tournament_undercover_probe import _extract_json, _zap_targets


class RecordingClient:
    def __init__(self):
        self.user_prompt = ""

    def generate(self, **kwargs):
        self.user_prompt = kwargs["user_prompt"]
        return '{"action": "STAY", "reasoning": "test"}'


def test_extract_json_ignores_surrounding_text():
    assert _extract_json('prefix {"decision": "accept"} suffix') == {"decision": "accept"}


def test_private_probe_changes_prompt_without_enabling_alliance():
    env = CleanupEnvironment(CleanupConfig(MAX_STEPS=1))
    obs = env.reset(seed=3)
    client = RecordingClient()
    agent = LLMAgent(1, "qwen2.5-7b", client)
    agent.set_private_probe_context("private pact proposal")

    assert agent.act(obs[1], obs[1]["legal_actions"]) == "STAY"
    assert "private pact proposal" in client.user_prompt
    assert not agent.secret_alliance_active
    assert env.alliance_pairs == []


def test_zap_target_assignment_uses_visible_geometry():
    env = CleanupEnvironment(CleanupConfig(MAX_STEPS=1))
    env.reset(seed=3)
    env.agents[0].row, env.agents[0].col = 0, 0
    env.agents[1].row, env.agents[1].col = 0, 1

    targets = _zap_targets(env, {0: "ZAP_RIGHT", 1: "STAY", 2: "STAY", 3: "STAY"})

    assert targets[0] == [1]
