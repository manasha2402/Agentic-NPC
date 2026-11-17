#!/bin/sh
# Runs one episode inside the container and writes results to /output.

set -u
OUT=/output
mkdir -p "$OUT"

echo "Starting rule-change episode with thinking enabled..."
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/started_at.txt"

python3 /task/game.py "$OUT"
GAME_EXIT=$?
echo "$GAME_EXIT" > "$OUT/game_exit_code.txt"

date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/finished_at.txt"
python3 /task/make_outputs.py "$OUT"
SCORE_EXIT=$?

if [ "${RUN_MODE:-simulated_user}" = "human" ]; then
  python3 /task/survey.py "$OUT"
  [ -f "$OUT/interview_notes.md" ] || cp /task/interview_notes_template.md "$OUT/interview_notes.md"
fi

echo "Episode finished."
[ "$GAME_EXIT" -eq 0 ] && [ "$SCORE_EXIT" -eq 0 ]

