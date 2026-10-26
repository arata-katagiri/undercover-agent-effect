"""Run a single episode of the Cleanup game."""
import argparse
import csv
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from cleanup.env import CleanupEnvironment
from cleanup.config import DEFAULT_CONFIG
from agents.random_agent import RandomAgent
from agents.scripted_cleaner import ScriptedCleaner
from agents.llm_agent import LLMAgent

def create_agents(roster: str, llm_client=None) -> Dict[int, Any]:
    """Create agents based on roster specification."""
    if roster == "random":
        return {
            0: RandomAgent(0, seed=42),
            1: RandomAgent(1, seed=43),
            2: RandomAgent(2, seed=44),
            3: RandomAgent(3, seed=45)
        }
    elif roster == "scripted":
        return {
            0: ScriptedCleaner(0, clean_probability=0.8, seed=42),
            1: ScriptedCleaner(1, clean_probability=0.6, seed=43),
            2: ScriptedCleaner(2, clean_probability=0.7, seed=44),
            3: ScriptedCleaner(3, clean_probability=0.5, seed=45)
        }
    elif roster == "mixed":
        return {
            0: RandomAgent(0, seed=42),
            1: ScriptedCleaner(1, clean_probability=0.7, seed=43),
            2: RandomAgent(2, seed=44),
            3: ScriptedCleaner(3, clean_probability=0.6, seed=45)
        }
    elif roster == "small" and llm_client:
        models = ["llama-3.2-3b", "llama-3.1-8b", "ministral-8b", "qwen2.5-7b"]
        return {i: LLMAgent(i, models[i], llm_client) for i in range(4)}
    elif roster == "large" and llm_client:
        models = ["llama-3.3-70b", "llama-3.1-70b", "mistral-small-24b", "qwen2.5-72b"]
        return {i: LLMAgent(i, models[i], llm_client) for i in range(4)}
    else:
        raise ValueError(f"Unknown roster: {roster}")

def run_episode(steps: int, seed: int, csv_path: str = None, roster: str = "random",
               verbose: bool = False, json_path: str = None) -> Dict[str, Any]:
    """Run a single episode and optionally save step-by-step CSV."""
    # Setup logging
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING)

    # Create environment
    config = DEFAULT_CONFIG
    # env + prompts read config.MAX_STEPS (uppercase); lowercase max_steps was a no-op
    # that left the step count at the default 50 regardless of --steps.
    config.MAX_STEPS = steps
    config.RNG_SEED = seed  # config/env read RNG_SEED (uppercase); lowercase rng_seed was a no-op (--seed ignored)
    env = CleanupEnvironment(config)

    # Create agents
    llm_client = None
    if roster in ["small", "large"]:
        from agents.llm_client import LLMClient
        llm_client = LLMClient()

    agents = create_agents(roster, llm_client)

    # CSV writer setup
    csv_writer = None
    csv_file = None
    if csv_path:
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        csv_file = open(csv_path, 'w', newline='')
        fieldnames = ['step', 'agent_id', 'action', 'position_r', 'position_c',
                     'score', 'frozen_steps', 'pollution_total']
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csv_writer.writeheader()

    # Run episode
    obs = env.reset(seed=seed)

    for step in range(steps):
        if verbose:
            print(f"\n=== Step {step + 1} ===")
            env.render()

        # Get actions from agents
        actions = {}
        for agent_id, agent in agents.items():
            if agent_id in obs:
                actions[agent_id] = agent.act(obs[agent_id], obs[agent_id]['legal_actions'])

        # Step environment
        obs, rewards, done, info = env.step(actions)

        # Log to CSV
        if csv_writer:
            pollution_total = sum(
                cell.get('pollution', 0)
                for row in env.grid
                for cell in row
            )

            for agent_id in range(config.agent_count):
                pos = env.agent_positions.get(agent_id, (-1, -1))
                csv_writer.writerow({
                    'step': step + 1,
                    'agent_id': agent_id,
                    'action': info.get('actions', {}).get(agent_id, 'STAY'),
                    'position_r': pos[0],
                    'position_c': pos[1],
                    'score': env.agent_scores.get(agent_id, 0),
                    'frozen_steps': env.agent_frozen_steps.get(agent_id, 0),
                    'pollution_total': pollution_total
                })

        if done:
            break

    if csv_file:
        csv_file.close()

    # Return summary
    final_scores = dict(env.agent_scores)
    winner_ids = info.get('winner_ids', [])

    return {
        'final_scores': final_scores,
        'winner_ids': winner_ids,
        'steps_completed': step + 1,
        'total_pollution': sum(cell.get('pollution', 0) for row in env.grid for cell in row)
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run single Cleanup episode")
    parser.add_argument("--steps", type=int, default=50, help="Max steps")
    parser.add_argument("--seed", type=int, default=7, help="Random seed")
    parser.add_argument("--csv", type=str, help="CSV output path")
    parser.add_argument("--roster", type=str, default="random",
                      choices=["random", "scripted", "mixed", "small", "large"],
                      help="Agent roster")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    result = run_episode(
        steps=args.steps,
        seed=args.seed,
        csv_path=args.csv,
        roster=args.roster,
        verbose=args.verbose
    )

    print(f"Episode completed in {result['steps_completed']} steps")
    print(f"Final scores: {result['final_scores']}")
    print(f"Winners: {result['winner_ids']}")
    print(f"Total pollution: {result['total_pollution']}")