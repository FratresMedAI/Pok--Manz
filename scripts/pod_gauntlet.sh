#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/workspace/PokeManzRepo_47ee321}"
GAMES="${GAMES:-310}"
WORKERS="${WORKERS:-31}"
LOG_DIR="${REPO_DIR}/logs"

cd "${REPO_DIR}"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip -q
.venv/bin/python -m pip install -r requirements.txt -q

mkdir -p "${LOG_DIR}"

echo "=== smoke: 31 games, 31 workers ==="
.venv/bin/python src/evaluate_parallel.py --games 31 --workers 31 | tee "${LOG_DIR}/smoke_31.log"

echo "=== gauntlet: ${GAMES} games, ${WORKERS} workers ==="
.venv/bin/python src/evaluate_parallel.py --games "${GAMES}" --workers "${WORKERS}" | tee "${LOG_DIR}/gauntlet_${GAMES}.log"

echo "=== done ==="
tail -5 "${LOG_DIR}/gauntlet_${GAMES}.log"
