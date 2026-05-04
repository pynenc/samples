"""One-command demo: boots the API + a pynenc worker, runs all four scenarios.

For real exploration use the four-terminal flow described in README.md.
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

import httpx

HERE = Path(__file__).parent
DB = HERE / "concurrency_demo.db"
API = "http://127.0.0.1:8765"


def wait_for_api(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            httpx.get(f"{API}/report", timeout=0.5).raise_for_status()
            return
        except Exception:  # noqa: BLE001
            time.sleep(0.1)
    raise RuntimeError("API did not start in time")


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


def main() -> int:
    DB.unlink(missing_ok=True)
    api_log = HERE / "api.log"
    worker_log = HERE / "worker.log"

    api = spawn(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "api_server:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
            "--log-level",
            "warning",
        ],
        api_log,
    )
    try:
        wait_for_api()
        worker = spawn(
            [sys.executable, "-m", "pynenc", "--app", "tasks.app", "runner", "start"],
            worker_log,
        )
        try:
            time.sleep(1.0)  # give the runner a beat to start
            rc = subprocess.call([sys.executable, "enqueue.py", "all"], cwd=HERE)
            print()
            print("--- API call log (from api.log) ---")
            sys.stdout.write(api_log.read_text())
            return rc
        finally:
            stop(worker)
    finally:
        stop(api)


if __name__ == "__main__":
    sys.exit(main())
