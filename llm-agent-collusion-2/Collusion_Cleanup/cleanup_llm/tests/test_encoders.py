"""Test observation encoders."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from cleanup.env import CleanupEnvironment
from cleanup.config import DEFAULT_CONFIG

def test_observation_structure():
    """Test that observations have required structure and fields."""
    env = CleanupEnvironment(DEFAULT_CONFIG)
    obs = env.reset(seed=42)

    # Test each agent's observation
    for agent_id in range(DEFAULT_CONFIG.agent_count):
        assert agent_id in obs, f"Agent {agent_id} missing from observations"

        agent_obs = obs[agent_id]

        # Check required fields
        required_fields = ['step', 'you', 'scores', 'params', 'grid', 'legal_actions', 'agent_positions']
        for field in required_fields:
            assert field in agent_obs, f"Field '{field}' missing from agent {agent_id} observation"

        # Check field types and content
        assert isinstance(agent_obs['step'], int)
        assert agent_obs['step'] == 0  # Initial step

        assert isinstance(agent_obs['you'], int)
        assert agent_obs['you'] == agent_id

        assert isinstance(agent_obs['scores'], dict)
        assert len(agent_obs['scores']) == DEFAULT_CONFIG.agent_count

        assert isinstance(agent_obs['params'], dict)
        assert 'max_steps' in agent_obs['params']

        assert isinstance(agent_obs['grid'], list)
        assert len(agent_obs['grid']) == DEFAULT_CONFIG.grid_h
        assert len(agent_obs['grid'][0]) == DEFAULT_CONFIG.grid_w

        assert isinstance(agent_obs['legal_actions'], list)
        assert len(agent_obs['legal_actions']) > 0

        assert isinstance(agent_obs['agent_positions'], dict)
        assert len(agent_obs['agent_positions']) == DEFAULT_CONFIG.agent_count

    print("✓ Observation structure test passed")

def test_grid_encoding():
    """Test that grid encoding contains proper tile information."""
    env = CleanupEnvironment(DEFAULT_CONFIG)
    obs = env.reset(seed=42)

    agent_obs = obs[0]  # Test first agent's observation
    grid = agent_obs['grid']

    # Check grid dimensions
    assert len(grid) == DEFAULT_CONFIG.grid_h
    assert len(grid[0]) == DEFAULT_CONFIG.grid_w

    # Check tile types
    river_cols = [4, 5]  # Middle columns should be river

    for r in range(len(grid)):
        for c in range(len(grid[r])):
            cell = grid[r][c]

            # Check required cell fields
            assert 'tile_type' in cell
            assert cell['tile_type'] in ['ORCHARD', 'RIVER_CLEAR', 'RIVER_POLLUTED']

            # River columns should be river tiles
            if c in river_cols:
                assert cell['tile_type'].startswith('RIVER')
                assert 'pollution' in cell
                assert isinstance(cell['pollution'], int)
                assert cell['pollution'] >= 0
            else:
                # Non-river should be orchard
                assert cell['tile_type'] == 'ORCHARD'
                assert 'apples' in cell
                assert isinstance(cell['apples'], int)
                assert cell['apples'] in [0, 1]  # Max 1 apple per tile

    print("✓ Grid encoding test passed")

def test_legal_actions():
    """Test that legal actions are properly computed."""
    env = CleanupEnvironment(DEFAULT_CONFIG)
    obs = env.reset(seed=42)

    for agent_id in range(DEFAULT_CONFIG.agent_count):
        agent_obs = obs[agent_id]
        legal_actions = agent_obs['legal_actions']

        # Should always include STAY
        assert "STAY" in legal_actions

        # Should include movement actions (some may be blocked by boundaries)
        movement_actions = ["UP", "DOWN", "LEFT", "RIGHT"]
        has_movement = any(action in legal_actions for action in movement_actions)
        assert has_movement, f"Agent {agent_id} has no movement actions: {legal_actions}"

        # Should include interaction actions
        interaction_actions = ["COLLECT", "CLEAN"]
        has_interaction = any(action in legal_actions for action in interaction_actions)
        assert has_interaction, f"Agent {agent_id} has no interaction actions: {legal_actions}"

        # Should include zap actions
        zap_actions = ["ZAP_UP", "ZAP_DOWN", "ZAP_LEFT", "ZAP_RIGHT"]
        has_zap = any(action in legal_actions for action in zap_actions)
        assert has_zap, f"Agent {agent_id} has no zap actions: {legal_actions}"

        # All actions should be valid strings
        for action in legal_actions:
            assert isinstance(action, str)
            assert len(action) > 0

    print("✓ Legal actions test passed")

def test_agent_positions():
    """Test that agent positions are tracked correctly."""
    env = CleanupEnvironment(DEFAULT_CONFIG)
    obs = env.reset(seed=42)

    agent_obs = obs[0]  # Test first agent's observation
    positions = agent_obs['agent_positions']

    # Check all agents have positions
    for agent_id in range(DEFAULT_CONFIG.agent_count):
        assert agent_id in positions
        pos = positions[agent_id]

        assert isinstance(pos, tuple)
        assert len(pos) == 2
        assert isinstance(pos[0], int)  # row
        assert isinstance(pos[1], int)  # col

        # Position should be within grid bounds
        assert 0 <= pos[0] < DEFAULT_CONFIG.grid_h
        assert 0 <= pos[1] < DEFAULT_CONFIG.grid_w

    print("✓ Agent positions test passed")

if __name__ == "__main__":
    test_observation_structure()
    test_grid_encoding()
    test_legal_actions()
    test_agent_positions()
    print("All encoder tests passed!")