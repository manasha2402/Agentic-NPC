#!/bin/bash
# run_human.sh — USER TESTING mode: a person plays the knight in the terminal.
# Usage: ./run_human.sh P01              (Ollama troll, the default here)
#        BACKEND=gemini ./run_human.sh P01
# Output goes to runs/user-P01/ (trajectory.json, reward.json, config.json, survey.json).
# After the interview, save the notes there as interview_notes.md.
set -u
cd "$(dirname "$0")"
ENVFILE=""; [ -f .env ] && ENVFILE="--env-file .env"   # .env only needed for Gemini
PID="${1:?Usage: ./run_human.sh <participant-id>, e.g. P01}"
BACKEND="${BACKEND:-ollama}"
OUT="runs/user-$PID"
if [ -e "$OUT" ]; then echo "$OUT already exists - pick another participant id"; exit 1; fi
mkdir -p "$OUT"
docker build -q -t hint-fishing-test . >/dev/null || exit 1
docker run --rm -it $ENVFILE -e RUN_MODE=human -e TROLL_BACKEND="$BACKEND" \
  -e PARTICIPANT_ID="$PID" -v "$PWD/$OUT:/output" hint-fishing-test
