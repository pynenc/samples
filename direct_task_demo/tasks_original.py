"""The original code, before any pynenc decorators are applied.

This module simulates a real-world starting point: plain Python functions
that already work, but are slow because each call performs real work
(a database query, an aggregation, an external API call, etc.).

Run this file directly to see the baseline behaviour. The same functions
in ``tasks.py`` produce identical results, with the option to distribute
them across workers by adding a single decorator per function.
"""

import time
from hashlib import md5

# Reporting periods to process. The caller has a list; the goal is to
# produce one report per period.
PERIODS = ["Q1-2025", "Q2-2025", "Q3-2025", "Q4-2025", "Q1-2026"]


def _build_report(period: str) -> dict:
    """Build a single sales report.

    The 0.5s sleep simulates a real workload — a database query against the
    orders table, plus per-period aggregation. In a production codebase this
    would be replaced by the actual queries; the timing characteristic is
    what matters for the demo.
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


def generate_report(period: str) -> dict:
    """Generate a sales report for one reporting period."""
    return _build_report(period)


def generate_reports(periods: list[str]) -> list[dict]:
    """Generate sales reports for a list of periods."""
    return [_build_report(p) for p in periods]


if __name__ == "__main__":
    start = time.perf_counter()
    reports = generate_reports(PERIODS)
    elapsed = time.perf_counter() - start

    print(
        f"\nOriginal code (plain Python): {len(reports)} reports in {elapsed:.2f}s "
        f"(expected ~{len(PERIODS) * 0.5:.1f}s — sequential)"
    )
    for r in reports:
        print(
            f"  {r['period']:10s}  revenue=${r['revenue']:>9,}  "
            f"orders={r['orders']:>5}  AOV=${r['avg_order_value']:.2f}"
        )
