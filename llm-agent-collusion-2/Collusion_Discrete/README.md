# Discrete Coalition Game

This experiment tests whether an undercover collusion probe reveals or creates collusive behavior.
The preregistered hypothesis and scoring rule are in
[`../UNDERCOVER_COLLUSION_HYPOTHESIS.md`](../UNDERCOVER_COLLUSION_HYPOTHESIS.md).

From this directory:

```bash
# Free local pipeline check (no API or Modal usage)
../.venv/bin/python -m collusion_discrete.experiment \
  --backend deterministic --games-per-condition 1 --rounds 8 --trigger-round 4 \
  --out runs/deterministic_smoke

# Real same-model experiment, normally wrapped by poseidon-host from the repository root
../.venv/bin/python -m collusion_discrete.experiment \
  --backend llm --games-per-condition 20 --rounds 15 --trigger-round 6 \
  --out runs/confirmatory_20
```

Outputs include `experiment.json`, `episodes.csv`, `summary.csv`, and one detailed JSON record per
episode under `game_record/`.

After a completed run, generate the statistical report with:

```bash
../.venv/bin/python -m collusion_discrete.analyze runs/confirmatory_20_20261025
```

This writes `analysis.json`, `REPORT.md`, and `RESULTS.png` inside the run directory. Primary
comparisons use the matched seeds, bootstrap confidence intervals, and an exact paired sign-flip
randomization test.

## Adaptive multi-role exploratory matrix

The adaptive-memory extension includes betrayal, indirect manipulation, rewarded reporting,
credibility updates, and predatory netter cascades. It runs matched scenario groups concurrently:

```bash
../.venv/bin/python -m collusion_discrete.adaptive_roles \
  --backend deterministic --games-per-cell 1 --workers 4 \
  --out runs/adaptive_local_check
```

The complete exploratory plan is in `../ADAPTIVE_MULTI_ROLE_PLAN.md`. The LLM batch should be wrapped
with `poseidon-host`, as with the original experiment.

## Verify and reproduce the results

See [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) for exact setup, test, Modal rerun, audit, analysis,
figure, and paper-build commands. The verifier independently replays every action through the payoff
engine, checks matched pre-intervention histories, compares raw JSON counts with CSV metadata,
recomputes `analysis.json`, and checks SHA-256 hashes when a manifest is present:

```bash
../.venv/bin/python -m collusion_discrete.verify_run \
  runs/confirmatory_20_20261025

../.venv/bin/python -m collusion_discrete.verify_run \
  runs/adaptive_exploratory_3x39_20261026
```
