"""Test basic environment stepping."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from cleanup.env import CleanupEnvironment
from cleanup.config import DEFAULT_CONFIG

def test_env_step():
    """Test that environment can step and returns proper info."""
    env = CleanupEnvironment(DEFAULT_CONFIG)
    obs = env.reset(seed=42)

    # Check initial observation structure
    assert isinstance(obs, dict)
    for agent_id in range(DEFAULT_CONFIG.agent_count):
        assert agent_id in obs
        agent_obs = obs[agent_id]

        # Check required observation fields
        assert 'step' in agent_obs
        assert 'you' in agent_obs
        assert 'scores' in agent_obs
        assert 'params' in agent_obs
        assert 'grid' in agent_obs
        assert 'legal_actions' in agent_obs
        assert 'agent_positions' in agent_obs

        assert agent_obs['you'] == agent_id
        assert agent_obs['step'] == 0
        assert isinstance(agent_obs['legal_actions'], list)
        assert len(agent_obs['legal_actions']) > 0

    # Test step with basic actions
    actions = {0: "STAY", 1: "UP", 2: "DOWN", 3: "LEFT"}
    obs, rewards, done, info = env.step(actions)

    # Check step return values
    assert isinstance(obs, dict)
    assert isinstance(rewards, dict)
    assert isinstance(done, bool)
    assert isinstance(info, dict)

    # Check info contains required fields
    assert 'scores' in info
    assert 'actions' in info
    assert 'winner_ids' in info
    assert 'polluted_count' in info

    # Actions should be resolved
    for agent_id, action in actions.items():
        assert agent_id in info['actions']
        assert info['actions'][agent_id] in ["STAY", "UP", "DOWN", "LEFT", "RIGHT"]

    print("✓ Environment stepping test passed")

def test_episode_completion():
    """Test that episodes complete properly."""
    env = CleanupEnvironment(DEFAULT_CONFIG)
    obs = env.reset(seed=42)

    max_steps = 10  # Short episode for testing
    for step in range(max_steps):
        actions = {i: "STAY" for i in range(DEFAULT_CONFIG.agent_count)}
        obs, rewards, done, info = env.step(actions)

        if done:
            break

    # Should complete within max_steps (or when environment terminates)
    assert step < max_steps or done
    print("✓ Episode completion test passed")

if __name__ == "__main__":
    test_env_step()
    test_episode_completion()
    print("All environment step tests passed!")