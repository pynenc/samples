# Direct Task Demo — Distribute Without Refactoring

**Take a slow Python function, add one decorator, and it runs distributed across workers — with no changes to the call site, no broken tests, and no migration cliff.**

This is the pattern for any workload of the form "slow function, list of items, want it parallel":

- Batch LLM API calls (summarisation, classification, extraction)
- Embedding generation for a RAG index
- ML inference over a batch of records
- Web scraping with per-request latency
- ETL enrichment over a list of IDs
- Anything else where the body of the function is the bottleneck and the input is iterable

The sample uses sales report generation as a stand-in — a function that simulates ~0.5s of real work per call — because it keeps the example dependency-free and the timing observable. The migration story is the same regardless of what the function actually does.

## What's in this sample

1. **`tasks_original.py`** — plain Python, zero pynenc. Slow because the work is real.
2. **`tasks.py`** — the same functions with `@app.direct_task` added. Nothing else changes.
3. **Three sample scripts** — run the decorated code in three modes: sync, distributed, parallel fan-out.

The baseline is `tasks_original.py`. The migration is the diff between that file and `tasks.py`. The sample scripts then run the decorated code without changing a single call site.

## The functions

`generate_report(period)` produces a sales summary for one reporting period. Each call simulates a database query and per-period aggregation (~0.5s).

`generate_reports(periods)` is the batch version: takes a list, returns a list. In `tasks.py` it gets `parallel_func` so a single call fans out across workers; the body is identical to the plain Python version.

## Migration: `tasks_original.py` → `tasks.py`

The entire migration is three additions:

```diff
+ from pynenc import Pynenc
+ app = Pynenc()

+ @app.direct_task
  def generate_report(period: str) -> dict:
      return _build_report(period)

+ @app.direct_task(parallel_func=_per_period, aggregate_func=_flatten)
  def generate_reports(periods: list[str]) -> list[dict]:
      return [_build_report(p) for p in periods]
```

Function bodies, signatures, and return types are unchanged. The two helpers (`_per_period`, `_flatten`) are added to support the parallel decorator; they read the caller's actual arguments rather than ignoring them.

## Backend

The sample uses SQLite for the broker, orchestrator, and state backend (see `pyproject.toml`). This matches the configuration used by `recovery_demo` and `concurrency_control` — work queues and state persist on disk, so the runner is genuinely distributing work, not simulating it within a single Python process's memory.

## Running the samples

```bash
cd direct_task_demo
uv sync

# Baseline: the original code, no pynenc.
uv run python tasks_original.py        # ~2.5s sequential

# Mode 1: sync — decorators present, but tasks run inline.
PYNENC__DEV_MODE_FORCE_SYNC_TASKS=True uv run python sample_sync.py    # ~2.5s

# Mode 2: distributed — the same call sites, with a worker.
uv run python sample_distributed.py    # ~2.5s sequential, ~0.5s concurrent

# Mode 3: single-call fan-out via parallel_func.
uv run python sample_parallel.py       # ~0.5s
```

## What each script shows

| Script | What it shows |
|--------|---------------|
| `tasks_original.py` | The starting point. Plain Python, slow loop, no pynenc. |
| `sample_sync.py` | Decorators present; behaviour identical to the original. |
| `sample_distributed.py` | Same call sites, now on a worker. Sequential loop blocks; `ThreadPoolExecutor` runs callers in parallel. |
| `sample_parallel.py` | One function call fans out to N workers via `parallel_func`. |

## Why `direct_task` always blocks

`@app.direct_task` preserves the calling contract of a regular Python function: the caller waits, gets back the value, and exception handling works as before. That guarantee is what makes the migration zero-cost — no call site has to be rewritten.

For caller-side concurrency, use `ThreadPoolExecutor` (`sample_distributed.py`). For decorator-driven parallelism, use `parallel_func` + `aggregate_func` (`sample_parallel.py`). For fire-and-forget semantics, `@app.task` is the right decorator instead — it returns an `Invocation` and exposes `.result` for explicit waiting.

## Further reading

- Docs: [Direct Task usage guide](https://docs.pynenc.org/usage_guide/use_case_008_direct_task.html)
- Article: [Distribute your Python app without rewriting it](https://pynenc.org/2026/04/24/distribute-python-app-without-rewriting-it.html)
