#!/bin/bash
# Usage: ./run_human.sh P01

set -u
cd "$(dirname "$0")"
PARTICIPANT_ID="${1:?Usage: ./run_human.sh <participant-id>, e.g. P01}"
OUT="runs/user-$PARTICIPANT_ID"

if [ -e "$OUT" ]; then
  echo "$OUT already exists; choose another participant ID."
  exit 1
fi

mkdir -p "$OUT"
docker build -q -t rule-change-test . >/dev/null || exit 1
docker run --rm -it \
  -e RUN_MODE=human \
  -e PARTICIPANT_ID="$PARTICIPANT_ID" \
  -v "$PWD/$OUT:/output" \
  rule-change-test

