"""Sample 2 — Distributed mode: the same call sites, with real workers.

Run:
    uv run python sample_distributed.py

The ``ThreadRunner`` is started in a background thread before the first call.
Each ``generate_report(...)`` call submits work to the SQLite-backed broker
and blocks until the worker delivers a result. The call sites are byte-for-byte
identical to ``sample_sync.py`` and ``tasks_original.py``.

Two patterns are demonstrated:

1. **Sequential loop** — the same list comprehension as the original code.
   Each call blocks before the next starts, so wall time is approximately
   ``N * task_duration``. ``@app.direct_task`` always blocks the caller
   because that preserves the calling contract of a regular Python function:
   the caller waits, gets back the value, and exception handling works as
   before. That guarantee is what makes the migration zero-cost.

2. **Concurrent caller threads** — wrap the same calls in a
   ``ThreadPoolExecutor``. Each thread blocks on its own call, but the
   runner processes them in parallel. ``ThreadPoolExecutor`` is a standard
   Python concurrency pattern; it composes naturally with ``direct_task``.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import tasks


def run_sequential() -> None:
    start = time.perf_counter()
    reports = [tasks.generate_report(p) for p in tasks.PERIODS]
    elapsed = time.perf_counter() - start
    print(
        f"\nSequential calls on runner: {len(reports)} reports in {elapsed:.2f}s "
        f"(each call blocks before the next starts)"
    )


def run_concurrent() -> None:
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=len(tasks.PERIODS)) as pool:
        reports = list(pool.map(tasks.generate_report, tasks.PERIODS))
    elapsed = time.perf_counter() - start
    print(
        f"\nConcurrent caller threads: {len(reports)} reports in {elapsed:.2f}s "
        f"(N caller threads -> N workers running in parallel)"
    )
    for r in reports:
        print(
            f"  {r['period']:10s}  revenue=${r['revenue']:>9,}  "
            f"orders={r['orders']:>5}  AOV=${r['avg_order_value']:.2f}"
        )


runner_thread = threading.Thread(target=tasks.app.runner.run, daemon=True)
runner_thread.start()
try:
    run_sequential()
    run_concurrent()
finally:
    tasks.app.runner.stop_runner_loop()
    runner_thread.join()
