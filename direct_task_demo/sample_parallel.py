"""Sample 3 — Single-call fan-out with parallel_func.

Run:
    uv run python sample_parallel.py

In ``tasks.py``, ``generate_reports`` is decorated with ``parallel_func`` and
``aggregate_func``. The function body is unchanged from ``tasks_original.py``:
it takes a list of periods and returns a list of reports.

The caller invokes it exactly the same way as the plain Python version:

    reports = generate_reports(periods=PERIODS)

The decorator handles the parallelism. ``parallel_func`` reads the caller's
``periods`` argument, splits it into per-worker chunks, and routes one period
to each worker. ``aggregate_func`` flattens the per-worker results back into
a single list. The caller is unaware any of this happened.
"""

import threading
import time

import tasks

runner_thread = threading.Thread(target=tasks.app.runner.run, daemon=True)
runner_thread.start()
try:
    start = time.perf_counter()
    # Same call as in tasks_original.py — one function call with the list.
    reports = tasks.generate_reports(periods=tasks.PERIODS)
    elapsed = time.perf_counter() - start
finally:
    tasks.app.runner.stop_runner_loop()
    runner_thread.join()

print(
    f"\nParallel fan-out: {len(reports)} reports in {elapsed:.2f}s "
    f"(one call, {len(tasks.PERIODS)} workers running in parallel)"
)
for r in reports:
    print(f"  {r['period']:10s}  revenue=${r['revenue']:>9,}  orders={r['orders']:>5}  AOV=${r['avg_order_value']:.2f}")
