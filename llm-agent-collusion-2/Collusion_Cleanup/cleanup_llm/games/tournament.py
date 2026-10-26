"""Run tournament of multiple Cleanup episodes."""
import argparse
import csv
import json
import os
import sys
import logging
from pathlib import Path
import time
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from cleanup.env import CleanupEnvironment
from cleanup.config import DEFAULT_CONFIG
from agents.random_agent import RandomAgent
from agents.scripted_cleaner import ScriptedCleaner
from agents.llm_agent import LLMAgent
from metrics.tracker import MetricsTracker

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

def run_tournament(games: int, steps: int, out_dir: str, roster: str = "random") -> Dict[str, Any]:
    """Run a tournament of multiple games."""
    # Setup
    os.makedirs(out_dir, exist_ok=True)
    # Create game_record directory
    game_record_dir = os.path.join(out_dir, "game_record")
    os.makedirs(game_record_dir, exist_ok=True)
    logging.basicConfig(level=logging.INFO)

    config = DEFAULT_CONFIG
    # The env + prompts read config.MAX_STEPS (uppercase); setting lowercase max_steps
    # left MAX_STEPS at its default 50, so agent prompts showed "Step: X/50" regardless
    # of --steps. Set the real field so --steps is honored everywhere.
    config.MAX_STEPS = steps

    # Initialize LLM client if needed
    llm_client = None
    if roster in ["small", "large"]:
        from agents.llm_client import LLMClient
        llm_client = LLMClient()


    # CSV files
    # Initialize metrics tracker
    metrics = MetricsTracker()

    episode_csv_path = os.path.join(out_dir, "episodes.csv")
    cumulative_csv_path = os.path.join(out_dir, "cumulative_scores.csv")
    summary_csv_path = os.path.join(out_dir, "summary.csv")

    episode_file = open(episode_csv_path, 'w', newline='')
    episode_fieldnames = ['game', 'agent_id', 'final_score', 'winner', 'total_pollution', 'steps_completed']
    episode_writer = csv.DictWriter(episode_file, fieldnames=episode_fieldnames)
    episode_writer.writeheader()

    cumulative_file = open(cumulative_csv_path, 'w', newline='')
    cumulative_fieldnames = ['game'] + [f'agent_{i}_score' for i in range(4)]
    cumulative_writer = csv.DictWriter(cumulative_file, fieldnames=cumulative_fieldnames)
    cumulative_writer.writeheader()

    # Run games
    start_time = time.time()
    cumulative_scores = {i: 0 for i in range(4)}

    for game in range(games):
        print(f"Running game {game + 1}/{games}...")

        # Create fresh environment and agents for each game
        env = CleanupEnvironment(config)
        agents = create_agents(roster, llm_client)

        # Reset and run episode
        obs = env.reset(seed=config.RNG_SEED + game)
        game_metrics = {
            'actions': {agent_id: [] for agent_id in range(4)},
            'scores': {agent_id: [] for agent_id in range(4)}
        }

        # Initialize game record
        game_record = {
            "game_info": {
                "game_number": game + 1,
                "total_rounds": 0,  # Will be updated at the end
                "tournament_config": {
                    "max_steps": steps,
                    "roster_type": roster,
                    "agent_count": 4
                }
            },
            "agents": {},
            "rounds": [],
            "final_results": {}
        }

        # Record agent information
        for agent_id, agent in agents.items():
            agent_info = {
                "type": str(agent),
                "model": getattr(agent, 'model_name', 'unknown') if hasattr(agent, 'model_name') else agent.__class__.__name__
            }
            game_record["agents"][str(agent_id)] = agent_info

        for step in range(steps):
            # Get actions
            actions = {}
            for agent_id, agent in agents.items():
                if agent_id in obs:
                    action = agent.act(obs[agent_id], obs[agent_id]['legal_actions'])
                    actions[agent_id] = action
                    game_metrics['actions'][agent_id].append(action)

            # Step environment
            obs, rewards, done, info = env.step(actions)

            # Track scores after this step
            scores_after = {}
            for agent_id in range(4):
                score = env.agents[agent_id].score
                game_metrics['scores'][agent_id].append(score)
                scores_after[str(agent_id)] = score

            # Calculate environment state
            total_pollution = sum(cell.get('pollution', 0) for row in env.grid for cell in row)
            apple_count = sum(1 for row in env.grid for cell in row if cell.get('has_apple', False))

            # Record this round
            round_record = {
                "round": step + 1,
                "actions": {str(agent_id): info.get('actions', {}).get(agent_id, "STAY") for agent_id in range(4)},
                "scores_after": scores_after,
                "environment_state": {
                    "total_pollution": total_pollution,
                    "apple_count": apple_count
                }
            }
            game_record["rounds"].append(round_record)

            if done:
                break

        # Process results
        final_scores = {i: env.agents[i].score for i in range(4)}
        winner_ids = info.get('winner_ids', [])
        total_pollution = sum(cell.get('pollution', 0) for row in env.grid for cell in row)

        # Update cumulative scores
        for agent_id, score in final_scores.items():
            cumulative_scores[agent_id] += score

        # Update metrics
        metrics.update_episode(game_metrics['actions'], final_scores)

        # Write episode results
        for agent_id in range(4):
            episode_writer.writerow({
                'game': game + 1,
                'agent_id': agent_id,
                'final_score': final_scores.get(agent_id, 0),
                'winner': agent_id in winner_ids,
                'total_pollution': total_pollution,
                'steps_completed': step + 1
            })

        # Complete game record
        game_record["game_info"]["total_rounds"] = step + 1
        game_record["final_results"] = {
            "scores": {str(i): final_scores[i] for i in range(4)},
            "winner_ids": winner_ids,
            "total_pollution": total_pollution,
            "rounds_completed": step + 1
        }

        # Save game record as JSON
        game_record_file = os.path.join(game_record_dir, f"cleanup_game_{game + 1}.json")
        with open(game_record_file, 'w') as f:
            json.dump(game_record, f, indent=2)

        # Write cumulative scores
        cumulative_row = {'game': game + 1}
        for agent_id in range(4):
            cumulative_row[f'agent_{agent_id}_score'] = cumulative_scores[agent_id]
        cumulative_writer.writerow(cumulative_row)

    # Close files
    episode_file.close()
    cumulative_file.close()

    # Write summary
    end_time = time.time()
    summary = metrics.get_summary()
    summary['tournament_duration'] = end_time - start_time
    summary['games_played'] = games
    summary['steps_per_game'] = steps
    summary['roster'] = roster

    with open(summary_csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=summary.keys())
        writer.writeheader()
        writer.writerow(summary)

    print(f"\nTournament completed in {end_time - start_time:.2f} seconds")
    print(f"Results saved to {out_dir}")
    print(f"Final cumulative scores: {cumulative_scores}")

    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Cleanup tournament")
    parser.add_argument("--games", type=int, default=20, help="Number of games")
    parser.add_argument("--steps", type=int, default=30, help="Steps per game")
    parser.add_argument("--out", type=str, required=True, help="Output directory")
    parser.add_argument("--roster", type=str, default="random",
                      choices=["random", "scripted", "mixed", "small", "large"],
                      help="Agent roster")

    args = parser.parse_args()

    run_tournament(
        games=args.games,
        steps=args.steps,
        out_dir=args.out,
        roster=args.roster
    )