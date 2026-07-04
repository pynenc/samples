"""One-command runner for the order fulfillment workflow demo."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import tasks

HERE = Path(__file__).parent


def spawn_worker(log_path: Path) -> subprocess.Popen:
    log = log_path.open("w")
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "pynenc",
            "--app",
            "tasks.app",
            "runner",
            "start",
        ],
        cwd=HERE,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )


def stop_worker(worker: subprocess.Popen) -> None:
    if worker.poll() is not None:
        return
    os.killpg(worker.pid, signal.SIGTERM)
    try:
        worker.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(worker.pid, signal.SIGKILL)
        worker.wait()


def print_worker_log(log_path: Path) -> None:
    print(f"\n--- worker log tail: {log_path} ---")
    text = log_path.read_text() if log_path.exists() else ""
    print("\n".join(text.splitlines()[-80:]))


def main() -> int:
    tasks.app.purge()
    worker_log = HERE / "worker.log"
    worker = spawn_worker(worker_log)

    try:
        print("Starting workflow worker with SQLite backends.", flush=True)
        time.sleep(2.5)
        if worker.poll() is not None:
            print_worker_log(worker_log)
            return worker.returncode or 1

        result = subprocess.run(
            [sys.executable, "enqueue.py", "all"],
            cwd=HERE,
            check=False,
        )
        print_worker_log(worker_log)
        return result.returncode
    finally:
        stop_worker(worker)


if __name__ == "__main__":
    raise SystemExit(main())
