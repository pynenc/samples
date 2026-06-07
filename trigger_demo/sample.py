"""One-command trigger demo: boots a worker, runs all scenarios.

For real exploration use the two-terminal flow described in README.md.
This script exists so CI (and impatient readers) can run the whole demo with
``uv run python sample.py``.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import tasks

HERE = Path(__file__).parent


def spawn(cmd: list[str], log_path: Path) -> subprocess.Popen:
    log = log_path.open("w")
    return subprocess.Popen(
        cmd,
        cwd=HERE,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )


def stop(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    os.killpg(proc.pid, signal.SIGTERM)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)


def print_worker_log(log_path: Path, *, crashed: bool = False) -> None:
    """Print the useful end of the worker log and keep its path visible."""
    label = "worker crash log" if crashed else "worker log tail"
    print(f"\n--- {label}: {log_path} ---")
    log_text = log_path.read_text() if log_path.exists() else ""
    line_count = 100 if crashed else 40
    print("\n".join(log_text.splitlines()[-line_count:]))


def run_scenarios(worker: subprocess.Popen, worker_log: Path) -> int:
    """Run the producer and stop waiting immediately if the worker crashes."""
    worker_code = worker.poll()
    if worker_code is not None:
        print_worker_log(worker_log, crashed=True)
        return worker_code or 1

    producer = subprocess.Popen([sys.executable, "enqueue.py", "all"], cwd=HERE)
    while producer.poll() is None:
        worker_code = worker.poll()
        if worker_code is not None:
            producer.terminate()
            try:
                producer.wait(timeout=5)
            except subprocess.TimeoutExpired:
                producer.kill()
                producer.wait()
            print_worker_log(worker_log, crashed=True)
            return worker_code or 1
        time.sleep(0.1)
    return producer.returncode or 0


def main() -> int:
    tasks.app.purge()

    worker_log = HERE / "worker.log"
    worker = spawn(
        [
            sys.executable,
            "-m",
            "pynenc",
            "--app",
            "tasks.app",
            "runner",
            "start",
        ],
        worker_log,
    )
    try:
        # Give the runner enough time to import tasks, register triggers, and
        # finish its first atomic-services tick.
        time.sleep(3.0)
        rc = run_scenarios(worker, worker_log)
        if worker.poll() is None:
            print_worker_log(worker_log)
        return rc
    finally:
        stop(worker)


if __name__ == "__main__":
    sys.exit(main())
