# Trigger demo — declarative event-driven tasks

> Cron, events, status chains, exception compensation, and AND/OR composition
> — declared next to the task that reacts, no separate scheduler process,
> no broker sidecar, no callback-wiring code at the call site.

## The problem

Most distributed task frameworks give you a queue: put work in, workers pull
it out. Anything else — running on a schedule, reacting to another task's
result, retrying with a fallback, fan-out from an event — is glued on with a
separate scheduler process, manual callback wiring, or imperative
`if/else` logic inside the task body.

This sample is **not just a pynenc tutorial**. It uses pynenc's trigger
system as a lens to walk through the underlying CS / distributed-systems
concepts — and contrasts how each one is typically solved in other Python
task frameworks.

## CS / distributed-systems concepts covered

| # | Concept | What pynenc declaration shows it |
|---|---|---|
| 1 | **Polling vs. reactive** (Observer pattern) | `on_status(task)` replaces a manual `while inv.status != SUCCESS` loop |
| 2 | **Scheduled execution** (cron) | `on_cron("*/15 * * * *")` — no Beat process, no external `crontab` |
| 3 | **Event-driven pub/sub** | `app.trigger.emit_event(code, payload)` + `on_event(code)` |
| 4 | **Pipeline / chain composition** | `on_status(upstream)` with `with_args_from_status` |
| 5 | **Exception compensation** (Saga, reactive leg) | `on_exception(task, exception_types=...)` |
| 6 | **Composite AND conditions** | `.with_logic("and")` over multiple conditions of different kinds (status + result) |

### How other frameworks solve each one

| Concept | Celery | Dramatiq | Prefect | Airflow / OS cron |
|---|---|---|---|---|
| Polling vs. reactive | `.link(callback)` at call site (imperative) | `pipeline()`; conditions live in task body | `on_completion` hooks (closer; still imperative) | Hooks/callbacks per operator |
| Scheduled execution | Celery Beat (separate process) | None built in | `schedule_interval` per flow | The DAG itself; heavy ops cost |
| Pub/sub | Use Redis Pub/Sub or Kafka externally | Same | Events + automations (paid SaaS layer) | Sensors |
| Pipeline composition | `chain(a.s(), b.s())` at call time | `pipeline` | Inside a `@flow` function | DAG `>>` operator |
| Exception compensation | `.link_error()` at call site | In task body | `on_failure` hook | Trigger rules per operator |
| Composite AND/OR | None native — need a coordinator/Chord | None native | None native | Trigger rules approximate it |

The Saga pattern's *reactive* leg (run a follow-up when a step fails) is what
the trigger system covers. The *transactional* leg (multi-step distributed
transactions with deterministic rollback and resume across restarts) is
what pynenc's workflow system covers, in a separate sample and article.

## What's in the box

```text
trigger_demo/
├── pyproject.toml   # pynenc + SQLite backend + SQLite trigger
├── tasks.py         # PynencBuilder app + 10 tasks
├── events.py        # tiny CLI to fire named events into the trigger backend
├── enqueue.py       # runs scenarios A–F, prints what each one triggered
├── sample.py        # one-command demo: boots a worker, runs all scenarios
└── README.md
```

The whole story fits in `tasks.py` — every concept above is one decorator.

## Run it (one command)

```bash
uv sync
uv run python sample.py
```

Spawns a pynenc worker subprocess, runs the six scenarios, prints the
per-scenario report and the tail of the worker log, then tears down.

## Run it (the two-terminal way)

This is the version to use when you want to watch the worker logs as
triggers fire. Open two terminals in `samples/trigger_demo/`:

```bash
# Terminal 1 — the worker (also runs the atomic service)
uv run pynenc --app tasks.app runner start

# Terminal 2 — fire scenarios or events by hand
uv run python enqueue.py event_pubsub
uv run python enqueue.py compensation
uv run python enqueue.py all

# or fire raw events:
uv run python events.py feed_updated --source rss_live --count 8
uv run python events.py article_ingested --payload '{"article_id":"x-bad","kind":"regular","source":"manual"}'
```

Optional third terminal: `uv run pynenc monitor` and open
<http://127.0.0.1:8000>.
The trigger-driven tasks make for an interesting timeline: tasks appear
without anyone explicitly calling them.

## What you will see

```text
=== A. polling_vs_reactive ===
  Target invocation:   <invocation-id>
  Polling invocation:  <invocation-id>
  Reactive invocation: created from poll_target SUCCESS
  OK: polling_tasks observed completion; reactive_tasks +1

=== B. cron ===
  Declared:  ingest_feed       on_cron('*/15 * * * *')
  Declared:  archive_old_content  on_cron('0 2 * * *')
  No imperative scheduling code, no separate Beat process.

=== C. event_pubsub ===
  Emitting event: feed_updated {source: 'rss_live', count: 3}
  OK: ingest_feed +1, enrich_article SUCCESS +3

=== D. pipeline ===
  Emitting event: article_ingested {kind: 'breaking_news'}
  OK: notify_subscribers +1 (filter call_arguments={'kind': 'breaking_news'})

=== E. compensation ===
  Emitting event: article_ingested {article_id: '*-bad'}
  OK: alert_editorial +1 (on_exception(enrich_article, 'EnrichmentError'))

=== F. composite ===
  Emitting feed_updated count=3 (below threshold=5)
  generate_digest delta=0 (expected 0)
  Emitting feed_updated count=8 (above threshold=5)
  OK: generate_digest +1 (expected 1)
```

Three things to notice:

- The **caller never schedules anything downstream**. Every reaction is a
  declaration on the *reacting* task, not on the upstream caller.
- **One `feed_updated` event** triggers `ingest_feed`, which emits per-article
  `article_ingested` events. Each matching event creates its own
  `enrich_article` invocation. The event, not a caller, drives the fan-out.
- **Composite AND** works on heterogeneous conditions: a status condition
  AND a result-filter condition. `generate_digest` only fires when *both*
  evaluate to true on the same upstream invocation.

## Architecture

- **Backend:** SQLite (single file `trigger_demo.db`, no Redis, no Docker)
- **Trigger backend:** `SQLiteTrigger` — same file as the orchestrator
- **Runner:** `ThreadRunner`
- **External services:** none
- **Process layout (manual flow):** the worker, producer commands, and optional
  Pynmon process share one SQLite file
- **Process layout (`sample.py`):** the script spawns `pynenc runner start`
  as a subprocess, then runs `enqueue.py all`
- **Trigger registration:** `trigger_task_modules = ["tasks"]` makes the
  runner import this lazy-loaded task module at startup, before the atomic
  service evaluates its trigger conditions
- **Cross-process arguments:** `SQLiteClientDataStore` lets producer and
  worker processes share serialized invocation arguments such as the target
  passed to `wait_result_tasks`
- **Trigger evaluation cadence:** the atomic-service cycle is 0.6 seconds,
  runners check for a claim every 0.3 seconds, and the cron scheduler has a
  1-second minimum interval. These short values keep the demo compact;
  production defaults are minutes
- **Logging:** `tasks.py` uses `PynencBuilder.logging_level(...)`; workers
  default to `info`, while producer scripts set `DEMO_LOG_LEVEL=warning` before
  importing the app to keep their output focused

## What this is *not* (yet)

- **No deterministic multi-step transactions across trigger hops.** A trigger
  is a reaction; if the reacting task crashes, pynenc retries that task, but
  the chain is not a single transaction. For deterministic multi-step
  pipelines with resume-from-failure semantics, use pynenc's workflow system.
- **No built-in event replay.** Events fire and reach matching conditions
  once. Replay-on-restart is a separate concern.
- **No built-in back-pressure on event fan-out.** A batch of matching events
  can create one downstream invocation per event in the same atomic-service
  pass. Pair with `running_concurrency=KEYS` (see the
  [`concurrency_demo`](../concurrency_demo)) when downstream needs guarding.

## Map: scenario → file → concept

| Scenario | Code | Concept |
|---|---|---|
| `polling_vs_reactive` | `enqueue.py:scenario_polling_vs_reactive` | Observer pattern |
| `cron` | `tasks.py:ingest_feed`, `archive_old_content` | Declarative scheduling |
| `event_pubsub` | `tasks.py:ingest_feed`, `enrich_article` | Pub/sub fan-out via `emit_event` |
| `pipeline` | `tasks.py:notify_subscribers` | `on_status` with `call_arguments` filter |
| `compensation` | `tasks.py:alert_editorial` | `on_exception` (Saga reactive leg) |
| `composite` | `tasks.py:generate_digest` | `on_status` AND `on_result(filter)` |
