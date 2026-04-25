"""Sample 1 — Sync mode: the decorators are present but inert.

Run:
    PYNENC__DEV_MODE_FORCE_SYNC_TASKS=True uv run python sample_sync.py

Or equivalently, with the env var set programmatically (as below).

With ``dev_mode_force_sync_tasks`` enabled, ``@app.direct_task`` runs the
function inline in the calling thread — no runner, no broker traffic, no
database writes. The behaviour is identical to ``tasks_original.py``: same
call sites, same return values, same timing characteristic.

This is the mode for incrementally adding ``@app.direct_task`` across an
existing codebase: existing tests stay green because nothing changes at
runtime.
"""

import os

# Set before importing tasks so the app picks it up at construction time.
os.environ.setdefault("PYNENC__DEV_MODE_FORCE_SYNC_TASKS", "True")

import time  # noqa: E402

import tasks  # noqa: E402

# Belt-and-suspenders: ensure sync mode regardless of how the script is run.
tasks.app.conf.dev_mode_force_sync_tasks = True

start = time.perf_counter()
reports = [tasks.generate_report(p) for p in tasks.PERIODS]
elapsed = time.perf_counter() - start

print(
    f"\nSync mode: {len(reports)} reports in {elapsed:.2f}s "
    f"(expected ~{len(tasks.PERIODS) * 0.5:.1f}s — sequential, like the original)"
)
for r in reports:
    print(f"  {r['period']:10s}  revenue=${r['revenue']:>9,}  orders={r['orders']:>5}  AOV=${r['avg_order_value']:.2f}")
