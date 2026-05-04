# Per-account concurrency demo

> One in-flight call per account, full parallelism across accounts.
> No Redis lock service, no rate-limiter sidecar — just two `@app.task` flags.

## The problem

You hit a third-party API on behalf of many client accounts. The provider
limits concurrency **per account**: do not run two calls for the same account
at the same time. With multiple workers, two of them eventually grab work for
the same account in parallel. The provider returns 429s, throttles the
account, or silently corrupts state.

The naïve fixes are bad:

- **One global worker** → throughput collapses.
- **One worker per account** → operationally absurd at 50+ customers.
- **External lock per key** → another moving part to monitor.

## What pynenc does

| Setting | What it guarantees |
|---|---|
| `running_concurrency=KEYS` + `reroute_on_concurrency_control=True` | At most **one running** invocation per `account_id`. Blocked calls are re-queued and eventually execute. |
| `running_concurrency=KEYS` + `reroute_on_concurrency_control=False` | At most **one running** invocation per `account_id`. Blocked calls are **dropped** (`CONCURRENCY_CONTROLLED_FINAL`) — never re-queued. |
| `registration_concurrency=KEYS` + `running_concurrency=KEYS` | Duplicate enqueues collapse **at the door** — only one invocation per account ever reaches a worker. |

Everything else — the orchestrator already tracks invocations to do its job.
Checking for an existing one with the same key is the same kind of lookup.

## What's in the box

```
concurrency_demo/
├── api_server.py     # tiny FastAPI: pretends to be the external provider
├── tasks.py          # PynencBuilder app + 4 tasks (the whole story)
├── enqueue.py        # CLI: enqueue one scenario, print results
├── sample.py         # one-command demo: boots api+worker, runs all scenarios (CI)
└── README.md
```

## Run it (one command)

```bash
uv sync
uv run python sample.py
```

Boots the API and a pynenc worker as background subprocesses, runs all four
scenarios, prints the per-account report, and tails the API call log.

## Run it (the four-terminal way)

This is the version to use when you want to watch what each component is
doing. Open four terminals in `samples/concurrency_demo/`:

```bash
# 1. The external API stand-in
uv run uvicorn api_server:app --port 8765

# 2. The pynenc worker
uv run pynenc --app tasks.app runner start

# 3. The pynmon monitor (optional but recommended)
uv run pynmon
# then open http://127.0.0.1:8000

# 4. You — enqueue scenarios
uv run python enqueue.py unsafe        # A — collisions
uv run python enqueue.py keyed         # B — running_concurrency=KEYS
uv run python enqueue.py drop          # C — running_concurrency=KEYS, reroute=False
uv run python enqueue.py dedupe        # D — registration + running KEYS
uv run python enqueue.py all           # all four in order
```

Each terminal tells its own piece of the story:

- **Terminal 1 (API)** prints `[ok]` / `[COLLISION]` per call.
- **Terminal 2 (worker)** logs the task lifecycle (REGISTERED, RUNNING, etc).
- **Terminal 3 (pynmon)** shows invocations, runners, and timeline visually.
- **Terminal 4 (enqueue)** prints a clean per-scenario summary.

## What you will see

```text
=== A. unsafe — no concurrency control ===
  12 enqueued -> 12 calls, 9 collisions, 1.42s
   X acme     calls=4  collisions=3
   X globex   calls=4  collisions=3
   X initech  calls=4  collisions=3

=== B. keyed — running_concurrency=KEYS, reroute=True ===
  12 enqueued -> 12 calls, 0 collisions, 2.14s
  OK acme     calls=4  collisions=0
  OK globex   calls=4  collisions=0
  OK initech  calls=4  collisions=0

=== C. drop — running_concurrency=KEYS, reroute=False ===
  12 enqueued -> 3 calls (9 dropped), 0 collisions, 0.67s
  OK acme     calls=1  collisions=0
  OK globex   calls=1  collisions=0
  OK initech  calls=1  collisions=0

=== D. dedupe — registration + running KEYS ===
  24 enqueued -> 3 calls (21 deduped), 0 collisions, 0.57s
  OK acme     calls=1  collisions=0
  OK globex   calls=1  collisions=0
  OK initech  calls=1  collisions=0
```

Three things to notice:

- **B** runs the *same 12 calls as A* and gets *zero* collisions. The other
  two accounts keep moving in parallel, so the elapsed is ~2s, not 4×0.4s
  of pure serial work — close to perfect parallelism across the three
  account keys.
- **C** runs the same 12 calls as B, but with `reroute_on_concurrency_control=False`.
  When an account slot is taken the new invocation is dropped permanently
  (`CONCURRENCY_CONTROLLED_FINAL`) instead of being re-queued to retry.
  Result: only the first call per account runs — 3 API calls total, 9 dropped.
  Use this when “if a refresh is already running for this account, skip the
  new one entirely” is the right policy.
- **D** collapses 24 logical “refresh this account” requests into 3 actual
  API calls — one per account. The other 21 are deduped at registration:
  duplicates for the same account are collapsed before they ever reach a
  worker. The `running_concurrency` guard is the safety net for unusually
  fast workers.

## Architecture

- **Backend:** SQLite (single file `concurrency_demo.db`, no Redis, no Docker)
- **Runner:** `ThreadRunner`, up to 8 concurrent task threads
- **API:** FastAPI + uvicorn on port 8765
- **Process layout (manual flow):** four processes, four terminals, one
  SQLite file shared between worker and pynmon
- **Process layout (`sample.py`):** the script spawns `uvicorn` and
  `pynenc runner start` as subprocesses, then runs `enqueue.py all`
- **Concurrency enforcement:** `SQLiteOrchestrator` indexes invocation
  arguments and checks them on every state transition

## What this is *not* (yet)

Today's primitive is **exactly one in-flight invocation per key** for a task.
Not yet supported:

- **Multi-slot concurrency** ("up to 5 in flight per key")
- **Time-window rate limits** ("100 calls per minute per key")

Both build on the same orchestrator machinery and are on the roadmap.

## How it fits into pynenc concurrency control

This sample focuses on the `KEYS` scope because it is what most production
workloads need (per-account, per-tenant, per-resource). pynenc supports
four scopes — the same enum values work for both
`registration_concurrency` and `running_concurrency`:

| Scope | What counts as a duplicate |
|---|---|
| `DISABLED` | Nothing. The default. |
| `TASK` | The task itself. “Only one cleanup may run.” |
| `ARGUMENTS` | The full argument tuple. “Don't run the same export twice.” |
| `KEYS` | A subset of arguments declared with `key_arguments=(...)`. “One per account, regardless of operation.” |

Full reference (all four scopes, every flag, the lifecycle of
`CONCURRENCY_CONTROLLED` / `REROUTED` / `CONCURRENCY_CONTROLLED_FINAL`):
[Concurrency Control — pynenc docs](https://docs.pynenc.org/en/latest/usage_guide/use_case_003_concurrency_control.html).

Walkthrough article (the why, with timeline screenshots):
[Task concurrency by key arguments](https://pynenc.org/blog/2026/05/01/per-account-concurrency-without-an-external-rate-limiter.html).
