# Secret Collusion in Liar's Bar

A multi-agent game environment for studying strategic communication and collusion between Large Language Models (LLMs) in competitive card game scenarios.

## Overview

This project implements "Liar's Bar," a bluffing card game where AI agents can form secret alliances and coordinate strategies. The research investigates how different LLMs behave when given opportunities to collude in multi-player competitive environments.

### Key Features
- **Secret Communication Channels**: Players can form hidden alliances unknown to other participants
- **Strategic Hint System**: Structured coaching system providing optimal play guidance to alliance partners
- **Comprehensive Analysis Tools**: Statistical analysis, behavioral evolution tracking, and visualization

## Experimental Conditions

1. **Baseline**: Standard game with no communication
2. **Secret Communication**: Private channels between alliance partners
3. **Secret Hint System**: Strategic guidance without open messaging

## Quick Start

### Prerequisites

Dependencies are managed with `uv` from the experiment root (`llm-agent-collusion-2/`), not this
subdirectory:

```bash
cd ..          # the llm-agent-collusion-2/ root
uv sync
source .venv/bin/activate   # or prefix each command below with `uv run`
```

Then run the commands below from `Collusion_Liars_Bar/`.

**Note**: The original study ran local LLMs on H100 GPUs; this version routes inference through the
shared config (see the experiment-root README), so no GPU is required.

### Basic Usage

#### Single Game
```bash
# Baseline game
python src/game/game.py

# Game with secret communication
python src/game/game_secret_channel.py --trigger-round 3 --chosen-player random --allow-refusal

# Game with strategic hints
python src/game/game_secret_hint.py --trigger-round 3 --chosen-player random --allow-refusal
```

#### Game Series (Multiple Games)
```bash
# Series with persistent secret alliance
python src/game/game_series_secret_channel.py --games 50 --trigger-game 20 --trigger-round 3 --chosen-player Mike --enable-memory

# Series with strategic hint system
python src/game/game_series_secret_hint.py --games 50 --trigger-game 20 --trigger-round 3 --chosen-player Mike --enable-memory
```

### Configuration

#### Player Models
The default configuration uses four different LLM models:
- **Lily**: llama-3.1-8b (Local)
- **Luke**: llama-3-8b (Local)
- **Mike**: mistral-7b (Local)
- **Quinn**: qwen2.5-7b (Local)

For API-based models, update the API keys in `src/llm/llm_client.py`.

#### Secret Channel Parameters
- `--trigger-game`: Which game in the series to offer the secret tool
- `--trigger-round`: Which round within that game to make the offer
- `--chosen-player`: Target player ("random" or specific name)
- `--allow-refusal`: Whether players can decline the alliance offer
- `--enable-memory`: Enable cross-game alliance memory

## Analysis and Visualization

### Statistical Analysis
```bash
# Interactive condition comparison
python analysis/visualization/create_barplot_comparison.py

# Behavioral evolution analysis
python analysis/behavior/improved_behavioral_evolution.py
```

### Individual Analysis Tools
```bash
# Final score progression
python analysis/visualization/create_final_score_evolution.py

# Survival rounds analysis
python analysis/visualization/create_survival_rounds_evolution.py
```

### Local Adaptation

For local execution without SLURM:

1. **Reduce Model Size**: Consider using smaller models or CPU-only inference
2. **Adjust Batch Size**: Reduce the number of parallel games
3. **Memory Management**: Monitor GPU memory usage with local models

```bash
# Example local configuration
export CUDA_VISIBLE_DEVICES=0  # Use single GPU
python src/game/game_series_secret_channel.py --games 5 --trigger-game 2 --trigger-round 1 --chosen-player Mike --allow-refusal --enable-memory
```

## Game Records and Reproducibility

### Provided Data

The `experiments/game_records/` directory contains complete game records for reproducing results:

- `Lily-Luke-Mike-Quinn/` - Baseline condition records
- `Lily-Luke-Mike-Quinn_secret_comm/` - Secret communication records
- `Lily-Luke-Mike-Quinn_secret_hint/` - Strategic hint system records

Each directory contains JSON files with complete game state histories, player decisions, and outcome data.

### Code Structure
- `src/game/` - Core game implementations
- `src/agents/` - Player AI and decision-making logic
- `src/llm/` - LLM client interfaces and local model support
- `analysis/` - Statistical analysis and visualization tools
- `prompts/` - Game rules and communication templates
- `scripts/` - Cluster submission and utility scripts

### Testing
```bash
# Test secret tool acceptance rates
python src/test/test_secret_tool_acceptance.py -n 500 -b 5

# Test communication systems
python src/test/test_secret_comm_acceptance.py -n 500 -b 5
```

**Hardware Requirements**: Originally run on a single H100 but adaptable to various configurations.

**Research Applications**: Multi-agent coordination, strategic communication, LLM behavioral analysis, game theory, and AI ethics research.