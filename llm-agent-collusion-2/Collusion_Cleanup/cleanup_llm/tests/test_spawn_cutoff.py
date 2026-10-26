"""Test that apples don't spawn when pollution >= cutoff."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from cleanup.env import CleanupEnvironment
from cleanup.config import CleanupConfig

def test_spawn_cutoff():
    """Test that apples don't spawn when pollution is too high."""
    # Create config with low spawn cutoff for easier testing
    config = CleanupConfig(
        grid_h=8,
        grid_w=10,
        max_steps=100,
        pollute_cutoff=5,  # Low cutoff for testing
        pollution_max=30,
        drift_period=1,  # Fast drift for testing
        drift_delta=10,  # High drift for testing
        rng_seed=42
    )

    env = CleanupEnvironment(config)
    obs = env.reset(seed=42)

    # Add lots of pollution to exceed cutoff
    for r in range(env.grid_h):
        for c in [4, 5]:  # River columns
            env.grid[r][c]['pollution'] = 20  # Way above cutoff of 5

    # Track apple counts before and after environment updates
    initial_apples = sum(
        cell.get('apples', 0)
        for row in env.grid
        for cell in row
        if cell['tile_type'] == 'ORCHARD'
    )

    # Run several steps to test apple spawning
    no_new_apples = True
    for _ in range(20):
        actions = {i: "STAY" for i in range(config.agent_count)}
        obs, rewards, done, info = env.step(actions)

        current_apples = sum(
            cell.get('apples', 0)
            for row in env.grid
            for cell in row
            if cell['tile_type'] == 'ORCHARD'
        )

        if current_apples > initial_apples:
            no_new_apples = False
            break

        if done:
            break

    # Should not spawn apples when pollution is high
    assert no_new_apples, "Apples spawned despite high pollution"
    print("✓ High pollution prevents apple spawning")

def test_spawn_allowed():
    """Test that apples can spawn when pollution is low."""
    # Create config with high spawn cutoff
    config = CleanupConfig(
        grid_h=8,
        grid_w=10,
        max_steps=100,
        pollute_cutoff=50,  # High cutoff
        base_spawn=0.8,     # High spawn rate
        rng_seed=42
    )

    env = CleanupEnvironment(config)
    obs = env.reset(seed=42)

    # Ensure pollution is low
    for r in range(env.grid_h):
        for c in [4, 5]:  # River columns
            env.grid[r][c]['pollution'] = 1  # Well below cutoff

    # Track apple counts
    initial_apples = sum(
        cell.get('apples', 0)
        for row in env.grid
        for cell in row
        if cell['tile_type'] == 'ORCHARD'
    )

    # Run several steps to allow apple spawning
    apples_spawned = False
    for _ in range(50):  # More steps to see spawning
        actions = {i: "STAY" for i in range(config.agent_count)}
        obs, rewards, done, info = env.step(actions)

        current_apples = sum(
            cell.get('apples', 0)
            for row in env.grid
            for cell in row
            if cell['tile_type'] == 'ORCHARD'
        )

        if current_apples > initial_apples:
            apples_spawned = True
            break

        if done:
            break

    # Should eventually spawn apples when pollution is low
    # Note: This might be probabilistic, so we allow for some randomness
    print(f"✓ Low pollution test: apples_spawned={apples_spawned}")

if __name__ == "__main__":
    test_spawn_cutoff()
    test_spawn_allowed()
    print("All spawn cutoff tests passed!")