"""Pynenc tasks demonstrating per-account concurrency control.

Four tasks, four behaviours:

* ``call_unsafe``      — no control. Workers race; the API sees collisions.
* ``call_keyed``       — ``running_concurrency=KEYS`` + ``reroute=True``.
                         One in-flight call per account at a time; blocked
                         calls are re-queued and eventually run. All 12
                         enqueues complete, serial within each account.
* ``call_keyed_drop``  — ``running_concurrency=KEYS`` + ``reroute=False``.
                         When an account slot is taken the new invocation is
                         dropped (``CONCURRENCY_CONTROLLED_FINAL``). Only
                         the first call per account runs; the rest are gone.
* ``refresh_once``     — ``registration_concurrency=KEYS`` +
                         ``running_concurrency=KEYS``. Duplicate refreshes
                         for the same account collapse at enqueue time;
                         a live worker won’t create a second slot while one
                         is already running.
"""

from __future__ import annotations

import os

import httpx
from pynenc import PynencBuilder
from pynenc.conf.config_task import ConcurrencyControlType as Mode

API_URL = "http://127.0.0.1:8765"

# Worker process leaves this unset → INFO. Producer scripts set it to
# "warning" so their console stays clean.
LOG_LEVEL = os.environ.get("DEMO_LOG_LEVEL", "info")

app = (
    PynencBuilder()
    .app_id("concurrency_demo")
    .sqlite("concurrency_demo.db")
    .thread_runner(min_threads=1, max_threads=8)
    .logging_stream("stdout")
    .logging_level(LOG_LEVEL)
    .max_pending_seconds(3.0)
    .build()
)


def _hit(account_id: str, op: str, hold: float | None = None) -> str:
    params = {"hold": hold} if hold is not None else None
    r = httpx.post(f"{API_URL}/call/{account_id}/{op}", params=params, timeout=10.0)
    r.raise_for_status()
    return r.json()["outcome"]


@app.task
def call_unsafe(account_id: str, op: str) -> str:
    return _hit(account_id, op)


@app.task(
    running_concurrency=Mode.KEYS,
    key_arguments=("account_id",),
    reroute_on_concurrency_control=True,
)
def call_keyed(account_id: str, op: str) -> str:
    return _hit(account_id, op)


@app.task(
    running_concurrency=Mode.KEYS,
    key_arguments=("account_id",),
    reroute_on_concurrency_control=False,
)
def call_keyed_drop(account_id: str, op: str) -> str:
    """Slot taken → invocation is dropped, not re-queued."""
    return _hit(account_id, op)


@app.task(
    running_concurrency=Mode.KEYS,
    registration_concurrency=Mode.KEYS,
    key_arguments=("account_id",),
    reroute_on_concurrency_control=True,
)
def refresh_once(account_id: str) -> str:
    """Dedup at the door: duplicate enqueues for the same account collapse
    into a ``ReusedInvocation`` before a worker ever sees them.
    ``running_concurrency=KEYS`` is the safety net for unusually fast
    workers that pick up the first task before all duplicates register.
    """
    return _hit(account_id, "refresh")
