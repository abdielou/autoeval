#!/usr/bin/env python3
"""autoeval loop runner -- launches claude sessions with auto-restart.

Usage:
    python run-loop.py                # run with defaults
    python run-loop.py --timeout 45   # custom timeout in minutes

The agent runs a fixed number of iterations per session, then exits.
This script restarts it with a fresh context. A hard timeout acts
as a safety net in case the agent doesn't exit on its own.

Stop the loop: Ctrl+C once kills the current session.
               Ctrl+C again within 3 seconds stops the loop entirely.

Cross-platform: works on Linux, macOS, and Windows.
No dependencies beyond Python stdlib.
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime

# --- Configuration (set by autoeval Phase 6) ---
CLI = "claude"              # CLI command — change to "claudish" or other compatible CLI
MODEL = "{runner_model}"
EFFORT = "{effort}"
TIMEOUT_MINUTES = {timeout_minutes}
# ------------------------------------------------

current_process = None
last_interrupt = 0.0


def _kill_process():
    """Kill the current child process."""
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
    current_process = None


def run_session(session_num, timeout_minutes):
    """Launch a single claude session with a hard timeout."""
    global current_process
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"--- Session {session_num} starting ({now}) ---")

    cmd = [
        CLI,
        "--dangerously-skip-permissions",
        "--model", MODEL,
        "--effort", EFFORT,
        "--append-system-prompt-file", "program.md",
        "Resume the optimization loop. Check git log and progress.jsonl for experiment history, then continue iterating.",
    ]

    try:
        # On Windows, create the child in a new process group so Ctrl+C
        # only goes to Python, not the child. Python then kills the child
        # explicitly. Without this, both processes race to handle Ctrl+C
        # and Python's KeyboardInterrupt may not fire reliably.
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        current_process = subprocess.Popen(cmd, **kwargs)
        current_process.wait(timeout=timeout_minutes * 60)
    except subprocess.TimeoutExpired:
        print(f"Session {session_num} timed out after {timeout_minutes}m (safety net)")
        _kill_process()
    except KeyboardInterrupt:
        # Ctrl+C during session — kill the child, let main loop decide
        _kill_process()
        raise
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


def main():
    global last_interrupt

    parser = argparse.ArgumentParser(description="autoeval loop runner")
    parser.add_argument("--timeout", type=int, default=TIMEOUT_MINUTES,
                        help=f"timeout in minutes per session (default: {TIMEOUT_MINUTES})")
    args = parser.parse_args()

    print("=== autoeval loop runner ===")
    print(f"Model: {MODEL} | Effort: {EFFORT} | Timeout: {args.timeout}m per session")
    print("Ctrl+C once = kill session | Ctrl+C twice within 3s = stop loop")
    print()

    session = 0
    while True:
        session += 1
        try:
            run_session(session, args.timeout)
            time.sleep(2)
        except KeyboardInterrupt:
            now = time.time()
            if now - last_interrupt < 3.0:
                # Double Ctrl+C — stop the loop
                print()
                print(f"Loop stopped after {session} sessions.")
                print("To resume: python run-loop.py")
                print("To monitor: python monitor.py")
                sys.exit(0)
            else:
                # Single Ctrl+C — session killed, will restart
                last_interrupt = now
                print()
                print("Session killed. Restarting in 3s... (Ctrl+C again to stop loop)")
                try:
                    time.sleep(3)
                except KeyboardInterrupt:
                    print()
                    print(f"Loop stopped after {session} sessions.")
                    print("To resume: python run-loop.py")
                    print("To monitor: python monitor.py")
                    sys.exit(0)


if __name__ == "__main__":
    main()
