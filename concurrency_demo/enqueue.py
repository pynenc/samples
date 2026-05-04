"""Enqueue one demo scenario and print the result.

Run from inside ``samples/concurrency_demo`` after the API and the pynenc
worker are up::

    uv run python enqueue.py unsafe        # A — collisions
    uv run python enqueue.py keyed         # B — running_concurrency=KEYS, reroute=True
    uv run python enqueue.py drop          # C — running_concurrency=KEYS, reroute=False
    uv run python enqueue.py dedupe        # D — registration + running KEYS
    uv run python enqueue.py all           # run all four in order
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from collections.abc import Callable

import httpx

# Quiet pynenc's producer-side INFO chatter before importing tasks.
os.environ.setdefault("DEMO_LOG_LEVEL", "warning")

import tasks  # noqa: E402

API = "http://127.0.0.1:8765"
ACCOUNTS = ["acme", "globex", "initech"]
OPS = ["fetch_profile", "list_invoices", "refresh_usage", "update_metadata"]

# (label, task, payloads)
Scenario = tuple[str, Callable, list[dict[str, str]]]
SCENARIOS: dict[str, Scenario] = {
    "unsafe": (
        "A. unsafe — no concurrency control",
        tasks.call_unsafe,
        [{"account_id": a, "op": o} for a in ACCOUNTS for o in OPS],
    ),
    "keyed": (
        "B. keyed — running_concurrency=KEYS, reroute=True",
        tasks.call_keyed,
        [{"account_id": a, "op": o} for a in ACCOUNTS for o in OPS],
    ),
    "drop": (
        "C. drop — running_concurrency=KEYS, reroute=False",
        tasks.call_keyed_drop,
        # Same 12 payloads as B.  With reroute=False, when an account slot is
        # already taken the new invocation is dropped permanently instead of
        # being re-queued.  Only the first call per account executes.
        [{"account_id": a, "op": o} for a in ACCOUNTS for o in OPS],
    ),
    "dedupe": (
        "D. dedupe — registration + running KEYS",
        tasks.refresh_once,
        # 8 events per account fired in a tight sequential loop.
        # All 24 arrive before the worker's first poll cycle, so 7 per account
        # are collapsed at registration time; running_concurrency is the safety
        # net if the worker is unusually fast.
        [{"account_id": a} for a in ACCOUNTS for _ in range(8)],
    ),
}


def reset_api(label: str) -> None:
    httpx.post(f"{API}/reset", params={"label": label}, timeout=2.0).raise_for_status()


def report() -> dict:
    return httpx.get(f"{API}/report", timeout=2.0).json()


def print_summary(label: str, elapsed: float, n_enqueued: int, reduction_label: str = "deduped") -> None:
    rep = report()
    reduced = n_enqueued - rep["total_calls"]
    reduction = f" ({reduced} {reduction_label})" if reduced > 0 else ""
    print(f"\n=== {label} ===")
    print(
        f"  {n_enqueued} enqueued -> {rep['total_calls']} calls{reduction}, "
        f"{rep['total_collisions']} collisions, {elapsed:.2f}s"
    )
    for name, a in rep["accounts"].items():
        mark = " X" if a["collisions"] else "OK"
        print(f"  {mark} {name:<8} calls={a['calls']}  collisions={a['collisions']}")


def run(key: str) -> None:
    label, task, payloads = SCENARIOS[key]
    reset_api(label)
    started = time.time()
    invs = [task(**p) for p in payloads]
    n_dropped = 0
    for inv in invs:
        try:
            _ = inv.result
        except KeyError:
            # CONCURRENCY_CONTROLLED_FINAL: invocation was dropped (reroute=False).
            n_dropped += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  ! invocation error: {exc!r}", file=sys.stderr)
    reduction_label = "dropped" if n_dropped > 0 else "deduped"
    print_summary(label, time.time() - started, len(payloads), reduction_label)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=[*SCENARIOS, "all"])
    args = parser.parse_args()
    keys = list(SCENARIOS) if args.scenario == "all" else [args.scenario]
    for key in keys:
        run(key)


if __name__ == "__main__":
    main()
