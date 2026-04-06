#!/usr/bin/env python3
"""autoeval loop runner -- launches claude sessions with auto-restart.

Usage:
    python run-loop.py                # run with defaults
    python run-loop.py --timeout 45   # custom timeout in minutes

The agent runs a fixed number of iterations per session, then exits.
This script restarts it with a fresh context. A hard timeout acts
as a safety net in case the agent doesn't exit on its own.

Stop the loop: Ctrl+C (kills current session immediately)

Cross-platform: works on Linux, macOS, and Windows.
No dependencies beyond Python stdlib.
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime

# --- Configuration (set by autoeval Phase 6) ---
MODEL = "{runner_model}"
EFFORT = "{effort}"
TIMEOUT_MINUTES = {timeout_minutes}
# ------------------------------------------------

current_process = None


def run_session(session_num, timeout_minutes):
    """Launch a single claude session with a hard timeout."""
    global current_process
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"--- Session {session_num} starting ({now}) ---")

    cmd = [
        "claude",
        "--dangerously-skip-permissions",
        "--model", MODEL,
        "--effort", EFFORT,
        "--append-system-prompt-file", "program.md",
        "Resume the optimization loop. Check git log and progress.jsonl for experiment history, then continue iterating.",
    ]

    try:
        current_process = subprocess.Popen(cmd)
        current_process.wait(timeout=timeout_minutes * 60)
    except subprocess.TimeoutExpired:
        print(f"Session {session_num} timed out after {timeout_minutes}m (safety net)")
        _kill_process()
    except FileNotFoundError:
        print("Error: 'claude' command not found. Is Claude Code installed and on your PATH?")
        sys.exit(1)
    except Exception as e:
        print(f"Session {session_num} ended with error: {e}")
        _kill_process()
    finally:
        current_process = None

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"--- Session {session_num} ended ({now}) ---")
    print()


def _kill_process():
    """Kill the current child process and all its children."""
    global current_process
    if current_process is None:
        return
    try:
        current_process.terminate()
        try:
            current_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            current_process.kill()
            current_process.wait(timeout=5)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="autoeval loop runner")
    parser.add_argument("--timeout", type=int, default=TIMEOUT_MINUTES,
                        help=f"timeout in minutes per session (default: {TIMEOUT_MINUTES})")
    args = parser.parse_args()

    print("=== autoeval loop runner ===")
    print(f"Model: {MODEL} | Effort: {EFFORT} | Timeout: {args.timeout}m per session")
    print("Press Ctrl+C to stop")
    print()

    session = 0
    try:
        while True:
            session += 1
            run_session(session, args.timeout)
            # Brief pause between sessions
            time.sleep(2)
    except KeyboardInterrupt:
        print()
        print(f"Loop stopped by user during session {session}.")
        _kill_process()
        print("To resume: python run-loop.py")
        print("To monitor: python monitor.py")


if __name__ == "__main__":
    main()
