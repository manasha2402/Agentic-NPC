#!/bin/bash
# Build and run five fixed-script baseline episodes.
# Usage: ./run_all.sh [--force]

set -u
cd "$(dirname "$0")"

FORCE=0
if [ "${1:-}" = "--force" ]; then FORCE=1; fi

for i in 01 02 03 04 05; do
  if [ -e "runs/run-$i" ] && [ "$FORCE" -ne 1 ]; then
    echo "runs/run-$i already exists. Re-run with --force to replace baseline outputs."
    exit 1
  fi
done

docker build -t rule-change-test . || exit 1

for i in 01 02 03 04 05; do
  target="runs/run-$i"
  if [ -e "$target" ]; then rm -rf -- "$target"; fi
  mkdir -p "$target"
  echo "===== run-$i: Qwen3.5-2B, thinking on ====="
  docker run --rm -v "$PWD/$target:/output" rule-change-test || exit 1
done

echo "===== Summary ====="
for i in 01 02 03 04 05; do
  echo "run-$i: $(tr -d '\n ' < "runs/run-$i/reward.json")"
done

