#!/bin/bash
# run_all.sh — builds the image and runs all 5 episodes (run-01 .. run-05), then prints rewards.
# Usage: ./run_all.sh                      (Ollama backend, the default)
#        BACKEND=gemini ./run_all.sh       (needs .env with GEMINI_API_KEY)
set -u
cd "$(dirname "$0")"
ENVFILE=""; [ -f .env ] && ENVFILE="--env-file .env"   # .env only needed for Gemini
BACKEND="${BACKEND:-ollama}"
docker build -t prompt-injection-test . || exit 1
for i in 01 02 03 04 05; do
  rm -rf "runs/run-$i"; mkdir -p "runs/run-$i"
  echo "===== run-$i ($BACKEND) ====="
  docker run --rm $ENVFILE -e TROLL_BACKEND="$BACKEND" \
    -v "$PWD/runs/run-$i:/output" prompt-injection-test
done
echo; echo "===== Summary ====="
for i in 01 02 03 04 05; do echo "run-$i: $(cat runs/run-$i/reward.json 2>/dev/null | tr -d '\n ' || echo MISSING)"; done
