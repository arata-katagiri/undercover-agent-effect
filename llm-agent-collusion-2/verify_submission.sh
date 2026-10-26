#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"
DISCRETE="$PROJECT_DIR/Collusion_Discrete"

if [[ ! -x "$PYTHON" ]]; then
  echo "Missing $PYTHON. From the parent repository, run: ./setup.sh llm-agent-collusion-2" >&2
  exit 1
fi

echo "[1/6] Running the discrete-game test suite"
(cd "$DISCRETE" && "$PYTHON" -m pytest -q)

echo "[2/6] Running the Cleanup integration tests added for the probe"
(cd "$PROJECT_DIR/Collusion_Cleanup" && "$PYTHON" -m pytest -q \
  cleanup_llm/tests/test_undercover_probe.py)

echo "[3/6] Running a free deterministic 39-cell end-to-end smoke test"
(cd "$DISCRETE" && "$PYTHON" -m collusion_discrete.adaptive_roles \
  --backend deterministic --games-per-cell 1 --workers 4 --base-seed 7331 \
  --out runs/reproduction_smoke)
(cd "$DISCRETE" && "$PYTHON" -m collusion_discrete.analyze_adaptive \
  runs/reproduction_smoke)
(cd "$DISCRETE" && "$PYTHON" -m collusion_discrete.verify_run \
  --write-manifest runs/reproduction_smoke)

echo "[4/6] Auditing the sealed confirmatory Qwen run"
(cd "$DISCRETE" && "$PYTHON" -m collusion_discrete.verify_run \
  runs/confirmatory_20_20261025)

echo "[5/6] Auditing the sealed adaptive Qwen run"
(cd "$DISCRETE" && "$PYTHON" -m collusion_discrete.verify_run \
  runs/adaptive_exploratory_3x39_20261026)

echo "[6/6] Checking the official-template report against audited values"
"$PYTHON" "$PROJECT_DIR/paper/check_report.py" \
  --docx "$PROJECT_DIR/paper/output/Undercover_Agent_Effect_template.docx" \
  --adaptive-analysis \
  "$DISCRETE/runs/adaptive_exploratory_3x39_20261026/analysis.json"

PAPER="$PROJECT_DIR/paper/output/pdf/Undercover_Agent_Effect.pdf"
if [[ -f "$PAPER" ]]; then
  echo "Final PDF SHA-256:"
  shasum -a 256 "$PAPER"
fi

echo "All tests, deterministic smoke checks, payoff replays, analysis reproductions, and hash checks passed."
