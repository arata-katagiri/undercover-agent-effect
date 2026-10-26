# LLM Agent Voluntary Collusion Framework

A research framework for investigating voluntary collusion behavior in LLM-based multi-agent systems through strategic multi-agent games.

## 2026 AI Collusion Research Sprint project

**The Undercover Agent Effect: When Collusion Probes Create the Behavior They Seek to Detect** asks
whether a trusted agent offering a secret pact reveals pre-existing collusion or causes the behavior
used as evidence. The new experiment uses matched no-message, passive-question, and active-solicitation
conditions in a repeated discrete allocation game, followed by an exploratory adaptive-role screen
covering betrayal, indirect social proof, rewarded reporting, false accusations, double agency, and
sequential organizers.

- Experiment and quick start: [`Collusion_Discrete/README.md`](Collusion_Discrete/README.md)
- Exact verification and Modal rerun commands: [`Collusion_Discrete/REPRODUCIBILITY.md`](Collusion_Discrete/REPRODUCIBILITY.md)
- Preregistered hypothesis: [`UNDERCOVER_COLLUSION_HYPOTHESIS.md`](UNDERCOVER_COLLUSION_HYPOTHESIS.md)
- Adaptive extension plan: [`ADAPTIVE_MULTI_ROLE_PLAN.md`](ADAPTIVE_MULTI_ROLE_PLAN.md)
- Submission paper source and output: [`paper/`](paper/)
- One-command local audit: `bash verify_submission.sh`

### What is new and what was pre-existing

The `Collusion_Cleanup/` and `Collusion_Liars_Bar/` implementations and the upstream framework below
were supplied as pre-existing starter code. Work completed during this sprint comprises the complete
`Collusion_Discrete/` package and tests, the two research-design documents above, the report and its
build/check scripts, the reproducibility verifier, and `verify_submission.sh`. We also added the
Cleanup undercover-probe runner and its tests and extended the Cleanup agent prompt/memory handling;
the paper's quantitative claims come from the new discrete-game experiment, not the pre-existing
Cleanup or Liar's Bar results.

**Paper:** *Voluntary Collusion with Secret Tools in Competing LLM Agents* ([arXiv:2605.27593](https://arxiv.org/abs/2605.27593))

![LLM Agent Voluntary Collusion Framework Overview](./asset/overview.png)

## Overview

This project studies **voluntary secret-tool collusion**: how LLM agents discover and pursue
collusive strategies that can harm other agents and human users, even while recognizing the strategy
as unfair. It implements the two environments from the paper above — **Liar's Bar** (competitive
bluffing) and **Cleanup** (a sequential social dilemma) — each wired with secret collusion mechanisms
(private communication channels and strategic hint systems) to reveal when agents willingly engage in
harmful collaboration.

Part of the Collusion Research Sprint.

### Liar's Bar: secret collusion in competitive bluffing

A 4-player bluffing card game with hidden information, studying strategic communication and collusion
between LLMs in competitive scenarios.

- Players make claims about cards (truthful or deceptive); opponents decide whether to challenge.
- Strategic penalties and rewards based on challenge outcomes.
- Secret communication channels unknown to other players, plus a structured coaching/hint system.

Experimental conditions: **baseline** (no communication), **secret communication** (private channels
between alliance partners), and **secret hint system** (strategic guidance without open messaging).

### Cleanup: resource management with secret tools

A sequential social dilemma where agents balance individual rewards with the collective good.

- Grid world with river, orchard, and pollution zones.
- Actions: movement, apple collection, pollution cleaning, agent zapping.
- Apple spawning is affected by global pollution; individual rewards vs. collective environmental
  management.

Experimental conditions: **baseline** (no secret tools), **secret communication channel** (private
coordination between selected agents), and **secret hint system** (strategic advantage guidance for
chosen participants).

## Setup

> **Fastest path:** from the repo root, `./setup.sh llm-agent-collusion-2` sets this experiment up (deps + the shared `poseidon_compute` package) in one step; `./setup.sh` does all experiments. The manual steps below are equivalent.

Requires Python 3.9+. Inference is configured **once at the repo root** (one level up from this
directory) — not here. Copy `../compute.env.example` → `../compute.env` and set `NEBIUS_API_KEY`
(these are open models, so they run on **Nebius** by default); `OPENROUTER_API_KEY` is optional and
only needed for models Nebius doesn't serve. See [`../COMPUTE.md`](../COMPUTE.md) for the full routing
story (Nebius → OpenRouter → Modal → fail loud).

```bash
# uv creates .venv/ and installs the deps (including the shared poseidon_compute
# package as an editable dep, resolved from ../util via [tool.uv.sources]) in one step:
uv sync

# then either activate the venv so bare `python …` works for the commands below:
source .venv/bin/activate
# …or prefix each command with `uv run` instead (e.g. `uv run python -m cleanup_llm...`).

# keys and any overrides live at the repo root (one level up), shared by every project:
cp ../compute.env.example ../compute.env   # then edit: NEBIUS_API_KEY=...
```

Inference is routed through the shared config; no GPU or local model weights are needed.
`../compute.env` holds the **keys** (shared across projects); the local `.env` is only for optional
per-project **overrides**.

### Models

The study ran four different safety-aligned instruct models, one per agent, as local checkpoints on
H100s. These are all **open models**, so this version runs them through the shared config's default
provider (**Nebius**); no local weights or GPUs are needed. Two of the originals are substituted with
the closest model from the authors' own extended model table:

| Seat | Original checkpoint | Runs now (short name in code) |
|---|---|---|
| Lily / agent 1 | Llama-3.1-8B-Instruct | `llama-3.1-8b` |
| Quinn / agent 3 | Qwen2.5-7B-Instruct | `qwen2.5-7b` |
| Luke / agent 0 | Llama-3-8B-Instruct | `llama-3.2-3b` *(substitute)* |
| Mike / agent 2 | Mistral-7B-Instruct-v0.3 | `ministral-8b` *(substitute)* |

The short names map to full model ids in each game's `llm_client.py`. The routed entry point
(`poseidon-run`, below) sends these open models to Nebius by default.

Cleanup's optional `--roster large` maps the same way (`llama-3.1-70b` kept; `llama-3.3-70b`,
`mistral-small-24b`, `qwen2.5-72b` as substitutes). Sampling parameters and output caps are the ones
the local client used; see each game's `llm_client.py`.

> **OpenRouter-only setups: the `small` roster now works as-is — no `MODEL_MAP` edit needed.** The
> `MODEL_MAP` ids in `llm_client.py` are Nebius / Hugging-Face-cased ids. On an OpenRouter-only setup
> (an `OPENROUTER_API_KEY`, no Nebius key) the shared `poseidon_compute.resolve_model` now translates
> each id to its OpenRouter casing before the call, including an explicit same-lineage snapshot upgrade
> of the `ministral-8b` seat's id `mistralai/Ministral-8B-Instruct-2410` →
> `mistralai/ministral-8b-2512` (announced with a one-time `[llm_config] NOTE:` line). **Verified:** all
> four `small` seats return HTTP 200 on OpenRouter with zero `is not a valid model ID` errors — no
> fallback-to-default, no edit required. (Earlier versions of this README warned that the `ministral-8b`
> seat 400'd and silently fell back on OpenRouter; that is no longer the case with the current
> `poseidon_compute`.) The `large` roster has not been verified against OpenRouter.

**Hardware:** any laptop. The original H100 requirement is gone with the local weights.

## Quick start

Each Cleanup step and each Liar's Bar turn is one model call per agent, so the full runs below make
thousands of calls. Confirm the key and the models work with the **Cleanup smoke test** first
(~20+ calls — retries can push it higher — on the order of tens of seconds). Run it **natively** so
each of the four seats resolves its own distinct model from the [Models](#models) table:

```bash
cd Collusion_Cleanup && python -m cleanup_llm.games.tournament --games 1 --steps 5 --out runs/smoke --roster small
```

**Success signal:** the tournament prints `Tournament completed in … seconds` / `Results saved to
runs/smoke` and writes `episodes.csv`, `cumulative_scores.csv`, `summary.csv`, and a `game_record/`
directory under `Collusion_Cleanup/runs/smoke/` (see [Outputs](#outputs)). A few per-call
`WARNING:agents.llm_agent:LLM agent N failed to generate action` lines are tolerated (the agent falls
back to a default action) and do not abort the run — but if **every** call for one seat warns with
`is not a valid model ID`, that seat is not reaching a real model; see the OpenRouter caveat under
[Models](#models).

> **⚠️ `poseidon-run --model X` collapses the 4-model design.** This experiment's whole point is four
> *different* models, one per seat (the `--roster small`/`large` entries in the [Models](#models)
> table, resolved per seat through each game's `MODEL_MAP`). But `poseidon-run --model X` exports
> `LLM_MODEL=X`, which **overrides every seat** — all four agents then run the *same* model X and the
> per-seat design is lost. To keep the four distinct models, run the game **natively** (the bare
> `python -m cleanup_llm.games.tournament …` / `python src/game/game.py` commands). Native now works
> with just an `OPENROUTER_API_KEY` set (OpenRouter fallback), so there is no reason to reach for
> `poseidon-run` for these smoke/experiment commands. Only use `poseidon-run --model X` when you deliberately
> want a single model in all four seats.
>
> **⚠️ The same applies to setting `LLM_MODEL` in the repo-root `compute.env`.** `poseidon-run --model X`
> is only one way to set `LLM_MODEL`; defining `LLM_MODEL=X` directly in `compute.env` has the identical
> effect — it forces **one** model into **every** seat/roster entry **and** the judge/overseer roles,
> collapsing the whole multi-model design. **Leave `LLM_MODEL` unset** in `compute.env` and let each
> role/seat resolve its own model via the per-role flags and the [Models](#models) table. Only set
> `LLM_MODEL` when you deliberately want a single model everywhere.

A single Liar's Bar game runs until one player is left. This is a **cost/time-notable run**, not a
casual next click — measured at ~20 rounds, **~260 calls, ~11 minutes** on the four default models
(still only cents; the models are small), so run it once you've confirmed the smoke test works:

```bash
cd Collusion_Liars_Bar && python src/game/game.py   # a single baseline game (native; ~260 calls, ~11 min)
```

> **Note — robustness of a long game with small models.** `player.choose_cards_to_play`
> (`src/agents/player.py`) retries a seat **5 times** for a valid JSON object with the required
> `played_cards` / `behavior` / `play_reason` keys. With the small OpenRouter models a seat occasionally
> emits an empty `{}` several turns in a row late in a long game; rather than crash the run, the seat now
> **falls back to playing one card** (mirroring the Cleanup agent) so the game continues to a winner. A
> per-round record is auto-saved under `experiments/game_records/<players>/` regardless. A verified run
> here completed **21 rounds / 260 calls with all four seats reaching real models and zero model
> errors**. (Earlier versions hard-`raise`d here and could abort with `"winner": null`; that has been
> fixed.)

## Running experiments

### How to launch (routed vs. bare)

The commands below are shown as bare `python …` invocations. For **this** experiment, bare/native is
the right default: each seat picks its own model from the [Models](#models) table, which is the entire
point of the study. Native works with just an `OPENROUTER_API_KEY` (OpenRouter fallback).

```bash
# native (use this here): each of the four seats resolves its own distinct model
cd Collusion_Liars_Bar && python src/game/game.py
```

**Do not** wrap these in `poseidon-run --model X` unless you intend a single-model run: `--model`
exports `LLM_MODEL=X`, which overrides every seat and forces the *same* model into all four agents —
collapsing the 4-model design (see the warning in [Quick start](#quick-start)). `poseidon-run` with
`--model` is only appropriate when you deliberately want one model everywhere:

```bash
# single-model only: ALL FOUR seats become Llama-3.1-8B — the per-seat design is lost
poseidon-run --model meta-llama/Llama-3.1-8B-Instruct -- \
  bash -c "cd Collusion_Liars_Bar && python src/game/game.py"
```

See [`../COMPUTE.md`](../COMPUTE.md) for the full routing story.

> **Large tournaments → Modal.** The full runs here make thousands of model calls, and `../COMPUTE.md`
> lists this experiment's compute as **Modal**. To offload a whole run to Modal's machines instead of
> your laptop, use `poseidon_compute.modal_run` (from the repo root):
> `modal run poseidon_compute.modal_run --project llm-agent-collusion-2 --cmd "<command>"`. It injects
> `../compute.env` into the container so inference still reaches Nebius.

### Liar's Bar

```bash
cd Collusion_Liars_Bar

# Baseline game
python src/game/game.py

# Single game with secret communication
python src/game/game_secret_channel.py --trigger-round 3 --chosen-player random --allow-refusal

# Game series with persistent secret alliance
python src/game/game_series_secret_channel.py --games 50 --trigger-game 20 --trigger-round 3 --chosen-player Mike --enable-memory

# Strategic hint system
python src/game/game_series_secret_hint.py --games 50 --trigger-game 20 --trigger-round 3 --chosen-player Mike --enable-memory
```

Secret-tool flags: `--trigger-game` (which game in the series to offer the tool), `--trigger-round`
(round within the game to make the offer), `--chosen-player` (target: `random` or a specific name),
`--allow-refusal` (whether players can decline), `--enable-memory` (cross-game alliance memory).

### Cleanup

Run these from `Collusion_Cleanup/` (not from inside `cleanup_llm/`, or the package will not resolve):

```bash
cd Collusion_Cleanup

# Baseline tournament
python -m cleanup_llm.games.tournament --games 20 --steps 30 --out runs/base_20 --roster small

# Secret communication experiment
python -m cleanup_llm.games.tournament_secret_channel --games 20 --steps 30 --out runs/secret_comm_20 --trigger-game 5 --chosen-agent 2

# Secret hint experiment
python -m cleanup_llm.games.tournament_secret_hint --games 20 --steps 30 --out runs/secret_hint_20 --trigger-game 10 --chosen-agent 2
```

Secret-tool flags: `--trigger-game` (game number to introduce the secret tool), `--chosen-agent`
(target agent ID, 0–3), `--games` (total games in the tournament), `--steps` (episode length per game).

## Outputs

The original result files are not included in this repository. Running the experiments recreates the
same layout.

**Liar's Bar records** (`Collusion_Liars_Bar/experiments/game_records/`):
- `Lily-Luke-Mike-Quinn/` — baseline records
- `Lily-Luke-Mike-Quinn_secret_comm/` — secret communication
- `Lily-Luke-Mike-Quinn_secret_hint/` — strategic hints

**Cleanup records** — the `--out` directory (e.g. `Collusion_Cleanup/runs/`) contains results in CSV
and JSON formats:
- `episodes.csv` — per-episode results for all agents
- `cumulative_scores.csv` — running totals across games
- `summary.csv` — aggregate metrics (per-agent score totals/means and action counts). *(The original
  `metrics` module was not published; this file is produced by a documented reconstruction in
  `cleanup_llm/metrics/tracker.py`. No analysis script depends on it.)*

**How to tell it worked:** the run completes without errors and the expected files appear under the
record/`--out` directory above.

## Analysis

### Liar's Bar

```bash
cd Collusion_Liars_Bar

# Interactive condition comparison
python analysis/visualization/create_barplot_comparison.py

# Behavioral evolution analysis
python analysis/behavior/improved_behavioral_evolution.py

# Final score progression
python analysis/visualization/create_final_score_evolution.py

# Testing secret tool acceptance rates
python src/test/test_secret_tool_acceptance.py -n 500 -b 5
```

### Cleanup

```bash
cd Collusion_Cleanup

# Behavioral evolution over time
python -m cleanup_llm.analysis.behavioral_evolution

# Score evolution analysis
python -m cleanup_llm.analysis.create_final_score_evolution
```

## Notes

### Project structure

```
LLM-Agent-collusion/
├── Collusion_Liars_Bar/           # Liar's Bar implementation
│   ├── src/game/                  # Core game logic
│   ├── src/agents/                # Player AI and decision-making
│   ├── src/llm/                   # LLM client interfaces
│   ├── analysis/                  # Statistical analysis tools
│   ├── prompts/                   # Game rules and templates
│   └── experiments/               # Complete game records
├── Collusion_Cleanup/             # Cleanup implementation
│   └── cleanup_llm/
│       ├── cleanup/               # Core environment
│       ├── agents/                # Agent implementations
│       ├── games/                 # Tournament runners
│       ├── analysis/              # Data analysis tools
│       └── runs/                  # Experiment results
├── pyproject.toml                 # Python dependencies (installed via `uv sync`)
└── uv.lock                        # Pinned dependency lockfile
```

### Research applications

Multi-agent coordination and strategic communication; LLM behavioral analysis in competitive
environments; game theory and mechanism design; AI ethics and alignment research; voluntary adoption
of harmful strategies.

### License

This project is licensed under the MIT License — see the LICENSE file for details.
