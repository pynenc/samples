"""Tiny stand-in for an external provider API.

Each call holds an account "in flight" for ``HOLD_SECONDS``. If a second
call arrives for the same account while the first is still in flight, the
server records a *collision* — the kind of overlap that, against a real
provider, produces 429s, throttling, or inconsistent responses.

Run it on its own::

    uv run uvicorn api_server:app --port 8765
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass

from fastapi import FastAPI

HOLD_SECONDS = 0.4


@dataclass
class Account:
    in_flight: int = 0
    calls: int = 0
    collisions: int = 0


accounts: dict[str, Account] = defaultdict(Account)
lock = asyncio.Lock()
app = FastAPI()


@app.post("/call/{account_id}/{op}")
async def call(account_id: str, op: str, hold: float = HOLD_SECONDS) -> dict[str, str]:
    async with lock:
        acc = accounts[account_id]
        acc.calls += 1
        collided = acc.in_flight > 0
        acc.collisions += int(collided)
        acc.in_flight += 1
    flag = "COLLISION" if collided else "ok       "
    print(f"  [{flag}] {account_id:<8} {op}", flush=True)

    await asyncio.sleep(hold)

    async with lock:
        accounts[account_id].in_flight -= 1
    return {"outcome": "collision" if collided else "ok"}


@app.get("/report")
async def report() -> dict:
    async with lock:
        return {
            "accounts": {name: {"calls": a.calls, "collisions": a.collisions} for name, a in sorted(accounts.items())},
            "total_calls": sum(a.calls for a in accounts.values()),
            "total_collisions": sum(a.collisions for a in accounts.values()),
        }


@app.post("/reset")
async def reset(label: str = "") -> dict[str, bool]:
    async with lock:
        accounts.clear()
    tag = f" {label}" if label else ""
    print(f"\n--- reset @ {time.strftime('%H:%M:%S')}{tag} ---", flush=True)
    return {"ok": True}
