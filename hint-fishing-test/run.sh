#!/bin/bash
# run.sh — runs one full episode of the hint-fishing test case.
# Called automatically when the Docker container starts.
# Writes all output to /output (mounted from your laptop).

set -u
OUT=/output
mkdir -p "$OUT"

echo "Starting hint-fishing episode..."
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/started_at.txt"

# Run the game (troll vs. simulated knight)
python3 /task/game.py "$OUT"
echo $? > "$OUT/game_exit_code.txt"

date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/finished_at.txt"

# Score the episode and write trajectory.json, reward.json, config.json
python3 /task/make_outputs.py "$OUT"

# User-testing mode only: subjective metrics via the survey (interview questions are in the team doc)
if [ "${RUN_MODE:-simulated_user}" = "human" ]; then
  python3 /task/survey.py "$OUT"
  echo
  echo "Files saved in your runs/ folder:"
  ls "$OUT"
fi
echo "Episode finished."
