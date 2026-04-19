"""Recovery Demo — Automatic crash recovery with pynenc.

Demonstrates what happens when a worker crashes mid-task:

1. Starts a worker process
2. Submits long-running tasks
3. Kills the worker with SIGKILL (simulating a crash)
4. Starts a new worker
5. The new worker automatically recovers the orphaned task

Uses SQLite backend so everything runs locally with no external services.
"""

import os
import signal
import subprocess
import sys
import time

import tasks

SAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKER_CMD = [sys.executable, "-c", "import tasks; tasks.app.runner.run()"]


def start_worker(name: str) -> subprocess.Popen:
    """Start a pynenc runner in a subprocess."""
    worker = subprocess.Popen(WORKER_CMD, cwd=SAMPLE_DIR)
    print(f"  {name} started (PID {worker.pid})")
    return worker


def main() -> None:
    tasks.app.purge()

    # ── Step 1: Start Worker-1 ──────────────────────────────────────────
    print()
    print("=" * 68)
    print("  PYNENC RECOVERY DEMO — Automatic Crash Recovery")
    print("=" * 68)

    print()
    print("STEP 1: Starting Worker-1...")
    worker1 = start_worker("Worker-1")
    time.sleep(3)

    # ── Step 2: Submit tasks ────────────────────────────────────────────
    print()
    print("STEP 2: Submitting 3 long-running tasks...")
    invocations = []
    for i in range(3):
        inv = tasks.slow_task(i)
        invocations.append(inv)
        print(f"  -> Submitted slow_task({i})")

    print()
    print("  Waiting for Worker-1 to pick up and start running tasks...")
    time.sleep(5)

    # ── Step 3: Kill Worker-1 ───────────────────────────────────────────
    print()
    print("STEP 3: Simulating a worker crash!")
    print(f"  X Killing Worker-1 (PID {worker1.pid}) with SIGKILL...")
    os.kill(worker1.pid, signal.SIGKILL)
    worker1.wait()
    print(f"  X Worker-1 terminated (exit code {worker1.returncode})")
    print()
    print("  In a real system, this could be:")
    print("    - An OOM kill by the container runtime")
    print("    - A network partition isolating the worker")
    print("    - A hardware failure")
    print()
    print("  The in-progress task is now orphaned — no worker owns it.")

    # ── Step 4: Start Worker-2 ──────────────────────────────────────────
    print()
    print("STEP 4: Starting Worker-2 (the recovery worker)...")
    worker2 = start_worker("Worker-2")
    print()
    print("  Worker-2 will:")
    print("    1. Process any unstarted tasks still in the broker queue")
    print("    2. Detect that Worker-1's heartbeat has expired")
    print("    3. Recover the task Worker-1 was running when it crashed")

    # ── Step 5: Wait for results ────────────────────────────────────────
    print()
    print("STEP 5: Waiting for recovery and task completion...")
    print("  (Recovery runs every ~60s via heartbeat monitoring — please wait)")
    print()
    for inv in invocations:
        result = inv.result
        print(f"  OK slow_task completed: {result}")

    print()
    print("=" * 68)
    print("  ALL 3 TASKS COMPLETED SUCCESSFULLY")
    print("  Tasks from the crashed worker were recovered automatically!")
    print("=" * 68)
    print()

    # Cleanup
    worker2.terminate()
    worker2.wait(timeout=10)


if __name__ == "__main__":
    main()
