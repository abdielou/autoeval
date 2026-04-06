#!/usr/bin/env bash
# autoeval loop runner -- launches claude sessions with auto-restart
#
# Usage:
#   ./run-loop.sh              # run with defaults
#   ./run-loop.sh --timeout 45 # custom timeout in minutes
#
# The agent runs {max_iterations} iterations per session, then exits.
# This script restarts it with a fresh context. A hard timeout acts
# as a safety net in case the agent doesn't exit on its own.
#
# Stop the loop: Ctrl+C (waits for current session to finish gracefully)

set -euo pipefail

# --- Configuration (set by autoeval Phase 6) ---
MODEL="{runner_model}"
EFFORT="{effort}"
TIMEOUT_MINUTES="{timeout_minutes}"
# ------------------------------------------------

# Allow override via --timeout flag
while [[ $# -gt 0 ]]; do
  case $1 in
    --timeout) TIMEOUT_MINUTES="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

SESSION=0
TRAPPED=0

cleanup() {
  TRAPPED=1
  echo ""
  echo "Loop stopped by user after $SESSION sessions."
  echo "To resume: ./run-loop.sh"
  echo "To monitor: python monitor.py"
  exit 0
}

trap cleanup SIGINT SIGTERM

echo "=== autoeval loop runner ==="
echo "Model: $MODEL | Effort: $EFFORT | Timeout: ${TIMEOUT_MINUTES}m per session"
echo "Press Ctrl+C to stop"
echo ""

while [[ $TRAPPED -eq 0 ]]; do
  SESSION=$((SESSION + 1))
  echo "--- Session $SESSION starting ($(date)) ---"

  # Run claude with a hard timeout as safety net
  # timeout returns 124 if it kills the process, which is fine
  timeout "${TIMEOUT_MINUTES}m" claude \
    --dangerously-skip-permissions \
    --model "$MODEL" \
    --effort "$EFFORT" \
    --append-system-prompt-file program.md \
    "Resume the optimization loop. Check git log and progress.jsonl for experiment history, then continue iterating." \
    || true

  echo "--- Session $SESSION ended ($(date)) ---"
  echo ""

  # Brief pause between sessions to allow Ctrl+C
  sleep 2
done
