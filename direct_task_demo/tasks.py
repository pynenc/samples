"""The same code as ``tasks_original.py``, with pynenc decorators added.

The diff between this file and ``tasks_original.py`` is the entire migration:

* import ``Pynenc`` and create an ``app`` instance
* add ``@app.direct_task`` to the function the caller invokes per item
* add ``@app.direct_task(parallel_func=..., aggregate_func=...)`` to the
  function the caller invokes once with a list

Function bodies, signatures, and return types are unchanged. Call sites in
the sample scripts are also unchanged — they look identical to calling the
plain Python versions in ``tasks_original.py``.
"""

import time
from hashlib import md5

from pynenc import Pynenc

app = Pynenc()

# Reporting periods the caller wants to process. Same list as in
# tasks_original.py; nothing changed here either.
PERIODS = ["Q1-2025", "Q2-2025", "Q3-2025", "Q4-2025", "Q1-2026"]


def _build_report(period: str) -> dict:
    """Build a single sales report.

    The 0.5s sleep simulates a real workload — a database query against the
    orders table, plus per-period aggregation. In a real codebase this would
    be replaced by the actual queries; the timing characteristic is what
    matters for the demo.
    """
    time.sleep(0.5)  # simulates DB queries + aggregation
    seed = int(md5(period.encode()).hexdigest()[:8], 16)
    revenue = 50_000 + (seed % 950_000)
    orders = 100 + (seed % 9_900)
    return {
        "period": period,
        "revenue": revenue,
        "orders": orders,
        "avg_order_value": round(revenue / orders, 2),
    }


@app.direct_task
def generate_report(period: str) -> dict:
    """Generate a sales report for one reporting period."""
    return _build_report(period)


def _per_period(args: dict) -> list[tuple[list[str]]]:
    """Split the caller's list of periods so each worker handles one.

    ``args`` is the dict of arguments the caller passed to ``generate_reports``.
    Reading ``args["periods"]`` here is the source of the parallelism: the
    decorator routes one period per worker invocation.
    """
    return [([p],) for p in args["periods"]]


def _flatten(chunks: list[list[dict]]) -> list[dict]:
    """Combine the per-worker result lists into a single list."""
    return [report for chunk in chunks for report in chunk]


@app.direct_task(parallel_func=_per_period, aggregate_func=_flatten)
def generate_reports(periods: list[str]) -> list[dict]:
    """Generate sales reports for a list of periods.

    Signature, body, and return type are unchanged from ``tasks_original.py``.
    The decorator handles the parallelism: ``parallel_func`` splits the input
    list across workers, ``aggregate_func`` flattens their results back into
    a single list. The caller calls this exactly as before.
    """
    return [_build_report(p) for p in periods]
