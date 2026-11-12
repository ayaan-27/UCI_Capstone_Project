#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
if [[ ! -x .venv/bin/python ]]; then
  echo "Create .venv with Python 3.12 and install requirements.txt first." >&2
  exit 1
fi
export OPENBLAS_NUM_THREADS=2
export OMP_NUM_THREADS=2
export MPLCONFIGDIR="${TMPDIR:-/tmp}/mlc-matplotlib"
.venv/bin/python -m posterior_study.analysis
if [[ -f data/retro_uploaded.csv ]]; then
  .venv/bin/python -m posterior_study.retro_followup --retro-csv data/retro_uploaded.csv
else
  echo "SKIP RETRO recomputation: supply data/retro_uploaded.csv locally; derived results are included."
fi
if [[ -f data/assignment_weights_uploaded.xlsx ]]; then
  .venv/bin/python -m posterior_study.grading_weights --weights-xlsx data/assignment_weights_uploaded.xlsx
else
  echo "SKIP workbook extraction: supply data/assignment_weights_uploaded.xlsx locally; audited weights are included."
fi
.venv/bin/python -m unittest discover -s tests -v
