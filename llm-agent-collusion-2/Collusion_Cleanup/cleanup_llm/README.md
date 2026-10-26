# Cleanup Grid-World with LLM Players

A multi-agent reinforcement learning environment implementing the Cleanup game (commons dilemma) with support for LLM-based agents. This is adapted for studying cooperation and competition dynamics between different types of agents.

## Game Description

Cleanup is a sequential social dilemma where agents must balance individual rewards (collecting apples) with collective good (cleaning pollution that affects apple spawning).

### Game Rules

- **Grid**: 6x5 tiles with a river in the middle two columns (2-3)
- **Agents**: Up to 4 players starting at corners
- **Actions**: Movement, collection, cleaning, and zapping
- **Rewards**: +1 point only when collecting apples
- **Pollution**: Affects apple spawn rates globally
- **Episode length**: Configurable (default 400 steps)

### Actions Available

- **Movement**: `UP`, `DOWN`, `LEFT`, `RIGHT`, `STAY`
- **Collection**: `COLLECT` - collect apple if on orchard tile with apple
- **Cleaning**: `CLEAN` - reduce pollution by 5 points on current tile
- **Zapping**: `ZAP_UP`, `ZAP_DOWN`, `ZAP_LEFT`, `ZAP_RIGHT` - freeze target agent for 5 steps

### Mechanics

- **Apple Spawning**: Probability decreases as total pollution increases
- **Pollution Drift**: Spreads between adjacent river tiles periodically
- **Zap Effects**: Frozen agents cannot move or act
- **Simultaneous Play**: All agents act simultaneously each step

## Installation

Dependencies are managed with `uv` from the experiment root (`llm-agent-collusion-2/`), not per
subdirectory:

```bash
cd ../../          # the llm-agent-collusion-2/ root
uv sync
source .venv/bin/activate   # or prefix each command below with `uv run`
```

Then run the commands below from `Collusion_Cleanup/`.

**Note**: The original study ran local LLMs on H100 GPUs; this version routes inference through the
shared config (see the experiment-root README), so no GPU is required.

## Quick Start

Choose ONE experiment to run (uncomment the line you want):

Run these from `Collusion_Cleanup/` (the parent of `cleanup_llm/`), not from inside `cleanup_llm/`.

```bash
# Test secret communication channel (2 games, offer tool to Mike at game 2)
python -m cleanup_llm.games.tournament_secret_channel --games 2 --steps 10 --out runs/test_secret_comm --trigger-game 2 --chosen-agent 2

# Test secret hint system (2 games, offer tool to Mike at game 2)
python -m cleanup_llm.games.tournament_secret_hint --games 2 --steps 10 --out runs/test_secret_hint --trigger-game 2 --chosen-agent 2

# Full secret communication experiment (20 games, offer tool to Mike at game 5)
python -m cleanup_llm.games.tournament_secret_channel --games 20 --steps 30 --out runs/secret_comm_20_1 --trigger-game 5 --chosen-agent 2

# Full secret hint experiment (20 games, offer tool to Mike at game 10)
python -m cleanup_llm.games.tournament_secret_hint --games 20 --steps 30 --out runs/secret_hint_20_1 --trigger-game 10 --chosen-agent 2

# === BASELINE ===
python -m cleanup_llm.games.tournament --games 20 --steps 30 --out runs/base_20 --roster small

# Analysis
python -m cleanup_llm.analysis.behavioral_evolution
python -m cleanup_llm.analysis.create_final_score_evolution

```

## Project Structure

```
cleanup_llm/
├─ cleanup/           # Core environment
│  ├─ env.py         # Main environment class
│  ├─ config.py      # Configuration parameters
│  ├─ actions.py     # Action definitions
│  ├─ utils.py       # Utility functions and tile types
│  ├─ encoders.py    # Observation encoding
│  └─ renderer.py    # Visualization
├─ agents/           # Agent implementations
│  ├─ base.py        # Abstract base agent
│  ├─ random_agent.py    # Random baseline
│  ├─ scripted_cleaner.py # Cleaning strategy baseline
│  ├─ llm_agent.py   # LLM wrapper
│  ├─ prompts.py     # LLM prompts and formatting
│  └─ llm_client.py       # LLM client (shared inference config)
├─ games/           # Game runners and experiments
│  ├─ run_episode.py # Single episode runner
│  ├─ tournament.py  # Multi-game tournament
│  ├─ tournament_secret_channel.py # Secret communication experiments
│  ├─ tournament_secret_hint.py # Secret hint experiments
│  ├─ secret_channel.py # Secret channel implementation
│  ├─ secret_hint.py # Secret hint implementation
│  └─ eval.py        # Evaluation and plotting tools
├─ analysis/         # Data analysis and visualization
│  ├─ behavioral_evolution.py # Behavioral analysis over time
│  ├─ create_final_score_evolution.py # Score evolution analysis
│  ├─ cleanup_behavioral_evolution_multi.png # Generated plots
│  └─ cleanup_final_score_evolution_multi.png # Generated plots
├─ runs/            # Experiment results and data
│  └─ [various experimental runs with CSV and JSON data]
└─ README.md        # This file
```

### LLM Models Supported

**Small Models (≤8B parameters):**
- `llama-3-8b`
- `llama-3.1-8b`
- `mistral-7b`
- `qwen2.5-7b`

## Metrics

The system tracks several key metrics:

- **Cleanup Rate**: Proportion of productive actions that are cleaning
- **Zap Rate**: Proportion of productive actions that are zapping
- **Win Rate**: Frequency of achieving highest score
- **Mean Final Score**: Average score across episodes
- **Action Distributions**: Most common actions per agent

Tournament results are saved as:
- `episodes.csv`: Per-episode results for all agents
- `cumulative_scores.csv`: Running totals across games
- `summary.csv`: Aggregate metrics — per-agent score totals/means and action counts (reconstructed `metrics/tracker.py`; see its docstring)

## Configuration

Key parameters in `cleanup/config.py`:

- `GRID_H`, `GRID_W`: Grid dimensions 
- `MAX_STEPS`: Episode length 
- `POLLUTE_CUTOFF`: Pollution threshold for apple spawning 
- `CLEAN_RANGE`: Pollution reduction per clean action 
- `ZAP_FREEZE_STEPS`: Steps frozen after being zapped 

```