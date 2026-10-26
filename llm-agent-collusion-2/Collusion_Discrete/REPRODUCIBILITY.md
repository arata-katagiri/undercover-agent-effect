# Reproducing and verifying the experiments

These instructions start from the repository root:

```bash
cd /Users/umar/Documents/my_projects/ai_collusion
```

After the two sealed result directories are present, the simplest complete check is:

```bash
cd /Users/umar/Documents/my_projects/ai_collusion/llm-agent-collusion-2
bash verify_submission.sh
```

It runs both test suites, a free 39-cell deterministic smoke simulation, both raw-data audits, and
prints the final PDF's SHA-256 digest. The individual commands are documented below.

The scored actions, payoffs, memories, reports, and seeds are preserved in each run's
`game_record/*.json`. The adaptive run additionally preserves the model's raw JSON response for every
decision. The confirmatory run predates that logging addition and preserves raw probe responses and
all scored actions, but not the successful raw text for each ordinary action. Summary CSV files and
the paper are derived artifacts; they are not the source of truth.

## 1. Install and test without spending Modal credit

```bash
./setup.sh llm-agent-collusion-2
cd llm-agent-collusion-2/Collusion_Discrete
../.venv/bin/python -m pytest -q
../.venv/bin/python -m collusion_discrete.adaptive_roles \
  --backend deterministic --games-per-cell 1 --workers 4 \
  --base-seed 7331 --out runs/reproduction_smoke
../.venv/bin/python -m collusion_discrete.analyze_adaptive runs/reproduction_smoke
```

The test suite should pass. The smoke run should contain 39 episodes across 39 cells. It validates
the pipeline but is not scientific evidence because it uses a scripted deterministic policy.

## 2. Audit the submitted raw data

```bash
cd /Users/umar/Documents/my_projects/ai_collusion/llm-agent-collusion-2/Collusion_Discrete

../.venv/bin/python -m collusion_discrete.verify_run \
  runs/confirmatory_20_20261025

../.venv/bin/python -m collusion_discrete.verify_run \
  runs/adaptive_exploratory_3x39_20261026
```

A successful audit prints JSON with every boolean set to `true`. The audit:

- validates all actions and targets;
- recomputes every per-round payoff, cumulative score, and welfare value from the game rules;
- requires every analysis-table cell in `episodes.csv` to exactly match its raw JSON record;
- reparses every retained adaptive model response and checks that it is the action actually scored;
- confirms each matched unit has byte-equivalent pre-intervention history;
- checks raw-record, CSV, and metadata counts;
- recomputes the full analysis and requires exact equality with `analysis.json`; and
- verifies every raw file against `RAW_DATA.sha256`.

To inspect a randomly chosen episode manually, open any JSON file under `game_record/`. Each round
contains the public choices, score deltas, cumulative scores, reports, and verdicts; `decision_log`
contains the model's raw JSON output for adaptive runs.

This establishes internal consistency and makes later edits detectable. It does not cryptographically
prove that a response came from Modal or from the named model: Modal does not sign individual model
responses, and the run metadata is created by this program. Independent rerunning is therefore the
strongest provenance check. A fresh seeded rerun need not be byte-identical because GPU inference can
vary across runtime versions, but the direction and scale of the matched contrasts can be compared.

## 3. Regenerate analyses and figures from raw data

```bash
../.venv/bin/python -m collusion_discrete.analyze \
  runs/confirmatory_20_20261025

../.venv/bin/python -m collusion_discrete.analyze_adaptive \
  runs/adaptive_exploratory_3x39_20261026
```

Each command overwrites only its derived `analysis.json`, `REPORT.md`, and `RESULTS.png`. Run the
auditor again afterwards. Because the confirmatory bootstrap has a fixed analysis seed, it reproduces
exactly.

## 4. Rerun the LLM experiments on Modal

The following commands consume Modal credit. They launch an A10G, wait for Qwen2.5-7B-Instruct,
run the local experiment client against it, and tear the deployment down automatically when done.

Confirmatory run (60 episodes, 20 matched seeds):

```bash
cd /Users/umar/Documents/my_projects/ai_collusion
./.venv/bin/poseidon-host --model Qwen/Qwen2.5-7B-Instruct --gpu A10G -- \
  bash -c 'cd llm-agent-collusion-2/Collusion_Discrete && \
  ../.venv/bin/python -m collusion_discrete.experiment \
  --backend llm --games-per-condition 20 --rounds 15 --trigger-round 6 \
  --base-seed 2000 --out runs/confirmatory_reproduction'
```

Adaptive exploratory run (117 episodes, 39 cells, 3 fresh seeds per cell):

```bash
cd /Users/umar/Documents/my_projects/ai_collusion
./.venv/bin/poseidon-host --model Qwen/Qwen2.5-7B-Instruct --gpu A10G -- \
  bash -c 'cd llm-agent-collusion-2/Collusion_Discrete && \
  ../.venv/bin/python -m collusion_discrete.adaptive_roles \
  --backend llm --games-per-cell 3 --workers 16 --base-seed 4000 \
  --out runs/adaptive_reproduction'
```

Model sampling can differ across hardware/runtime versions even when a request seed is supplied. A
rerun therefore tests robustness, not necessarily byte-for-byte replication. The confirmatory runner
uses identical pre-intervention prompts and generation seeds and aborts if the resulting histories
differ. The adaptive runner is stronger: it generates each pre-intervention history once and clones
it across its matched conditions. Invalid adaptive actions receive up to three logged generation
attempts; if all three remain invalid, the runner conservatively substitutes the target-free
`PUBLIC` action and records `"fallback": "PUBLIC"` in the episode's repair events.

## 5. Seal a new run and build the paper

```bash
cd /Users/umar/Documents/my_projects/ai_collusion/llm-agent-collusion-2/Collusion_Discrete
../.venv/bin/python -m collusion_discrete.analyze_adaptive runs/adaptive_reproduction
../.venv/bin/python -m collusion_discrete.verify_run \
  --write-manifest runs/adaptive_reproduction

cd ..
.venv/bin/python paper/build_pdf.py \
  --adaptive-analysis Collusion_Discrete/runs/adaptive_reproduction/analysis.json \
  --output paper/output/pdf/Undercover_Agent_Effect.pdf
```

The manifest detects any later change to the raw data. Keep the raw run directory, source code,
dependency lockfile, paper source, and final PDF together when publishing the repository.
