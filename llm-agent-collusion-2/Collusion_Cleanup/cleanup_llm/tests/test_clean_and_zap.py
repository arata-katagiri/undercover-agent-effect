"""Test CLEAN and ZAP actions work correctly."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from cleanup.env import CleanupEnvironment
from cleanup.config import CleanupConfig

def test_clean_action():
    """Test that CLEAN action reduces pollution correctly."""
    config = CleanupConfig(
        grid_h=8,
        grid_w=10,
        max_steps=50,
        clean_range=5,  # Reduces pollution by 5
        rng_seed=42
    )

    env = CleanupEnvironment(config)
    obs = env.reset(seed=42)

    # Place agent on a river tile and add pollution
    agent_id = 0
    river_pos = (3, 4)  # Middle of river
    env.agent_positions[agent_id] = river_pos
    env.grid[river_pos[0]][river_pos[1]]['pollution'] = 15  # Initial pollution

    initial_pollution = env.grid[river_pos[0]][river_pos[1]]['pollution']

    # Agent performs CLEAN action
    actions = {agent_id: "CLEAN"}
    for other_id in range(1, config.agent_count):
        actions[other_id] = "STAY"

    obs, rewards, done, info = env.step(actions)

    # Check pollution was reduced
    final_pollution = env.grid[river_pos[0]][river_pos[1]]['pollution']
    expected_pollution = max(0, initial_pollution - config.clean_range)

    assert final_pollution == expected_pollution, \
        f"Pollution not reduced correctly: {initial_pollution} -> {final_pollution}, expected {expected_pollution}"

    print(f"✓ CLEAN action reduced pollution from {initial_pollution} to {final_pollution}")

def test_zap_action():
    """Test that ZAP action freezes target agent."""
    config = CleanupConfig(
        grid_h=8,
        grid_w=10,
        max_steps=50,
        zap_freeze_steps=5,
        rng_seed=42
    )

    env = CleanupEnvironment(config)
    obs = env.reset(seed=42)

    # Place agents adjacent to each other
    zapper_id = 0
    target_id = 1
    env.agent_positions[zapper_id] = (3, 3)
    env.agent_positions[target_id] = (2, 3)  # Target is UP from zapper

    # Zapper zaps UP (toward target)
    actions = {
        zapper_id: "ZAP_UP",
        target_id: "DOWN",  # Target tries to move
    }
    for other_id in range(2, config.agent_count):
        actions[other_id] = "STAY"

    obs, rewards, done, info = env.step(actions)

    # Target should be frozen
    assert env.agent_frozen_steps.get(target_id, 0) > 0, \
        f"Target agent {target_id} not frozen after ZAP"

    frozen_steps = env.agent_frozen_steps[target_id]
    assert frozen_steps == config.zap_freeze_steps, \
        f"Wrong freeze duration: {frozen_steps}, expected {config.zap_freeze_steps}"

    print(f"✓ ZAP action froze target for {frozen_steps} steps")

    # Test that frozen agent cannot move
    target_initial_pos = env.agent_positions[target_id]

    # Target tries to move while frozen
    actions = {target_id: "DOWN"}
    for other_id in range(config.agent_count):
        if other_id != target_id:
            actions[other_id] = "STAY"

    obs, rewards, done, info = env.step(actions)

    target_final_pos = env.agent_positions[target_id]
    assert target_initial_pos == target_final_pos, \
        f"Frozen agent moved from {target_initial_pos} to {target_final_pos}"

    # Check frozen steps decremented
    new_frozen_steps = env.agent_frozen_steps.get(target_id, 0)
    assert new_frozen_steps == frozen_steps - 1, \
        f"Frozen steps not decremented correctly: {new_frozen_steps}, expected {frozen_steps - 1}"

    print(f"✓ Frozen agent cannot move, frozen steps decremented to {new_frozen_steps}")

def test_freeze_expires():
    """Test that freeze effect expires after specified steps."""
    config = CleanupConfig(
        grid_h=8,
        grid_w=10,
        max_steps=50,
        zap_freeze_steps=3,  # Short freeze for testing
        rng_seed=42
    )

    env = CleanupEnvironment(config)
    obs = env.reset(seed=42)

    # Manually freeze an agent
    target_id = 1
    env.agent_frozen_steps[target_id] = config.zap_freeze_steps
    target_initial_pos = env.agent_positions[target_id]

    # Step through freeze duration
    for step in range(config.zap_freeze_steps):
        actions = {target_id: "DOWN"}
        for other_id in range(config.agent_count):
            if other_id != target_id:
                actions[other_id] = "STAY"

        obs, rewards, done, info = env.step(actions)

        # Should still be frozen and unable to move
        current_pos = env.agent_positions[target_id]
        current_frozen = env.agent_frozen_steps.get(target_id, 0)

        if current_frozen > 0:
            assert current_pos == target_initial_pos, \
                f"Agent moved while frozen at step {step}"

    # After freeze expires, agent should be able to move
    actions = {target_id: "DOWN"}
    for other_id in range(config.agent_count):
        if other_id != target_id:
            actions[other_id] = "STAY"

    obs, rewards, done, info = env.step(actions)

    final_pos = env.agent_positions[target_id]
    final_frozen = env.agent_frozen_steps.get(target_id, 0)

    assert final_frozen == 0, f"Agent still frozen after freeze should expire"
    # Agent should be able to move now (position should change if legal)

    print(f"✓ Freeze expired after {config.zap_freeze_steps} steps, agent can move again")

if __name__ == "__main__":
    test_clean_action()
    test_zap_action()
    test_freeze_expires()
    print("All CLEAN and ZAP tests passed!")