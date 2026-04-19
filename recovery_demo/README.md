# Recovery Demo: Automatic Crash Recovery

## The Problem

Workers crash. Containers get OOM-killed. Network partitions happen. **Your tasks just vanish.**

With most task frameworks, a task in progress when a worker dies is simply lost. You need manual intervention, external monitoring, or custom retry scripts to detect and re-process failed work.

## What Pynenc Does Differently

Pynenc automatically recovers tasks from crashed workers using heartbeat-based dead-runner detection:

1. **Heartbeat monitoring** — each runner sends periodic heartbeats to the orchestrator
2. **Crash detection** — if a runner stops sending heartbeats, it is marked as inactive
3. **Automatic recovery** — tasks owned by inactive runners are detected, re-routed to the broker, and processed by a healthy runner

No manual intervention. No external monitoring. The system heals itself.

## How to Run

```bash
cd recovery_demo
uv sync
uv run python sample.py
```

## What to Observe

The demo runs through five steps:

| Step | What happens |
|------|-------------|
| 1 | **Worker-1 starts** — a runner process begins polling the broker |
| 2 | **3 tasks submitted** — long-running `slow_task` invocations are queued |
| 3 | **Worker-1 crashes** — killed with SIGKILL mid-execution (simulates OOM/hardware failure) |
| 4 | **Worker-2 starts** — a new runner begins processing |
| 5 | **Automatic recovery** — Worker-2 detects Worker-1's stale heartbeat, recovers the orphaned task, and completes all work |

Watch the logs for:
- `Recovering running invocation:... from inactive runner` — the recovery system detecting the orphaned task
- `[slow_task(N)] Starting` / `Finished` — tasks executing and completing after recovery
- Final confirmation that all 3 tasks completed successfully

## How It Works Under the Hood

```text
Worker-1 crashes                    Worker-2 starts
       |                                  |
       v                                  v
  task stuck in                    sends heartbeats
  RUNNING state                    picks up queued tasks
       |                                  |
       |     heartbeat expires            |
       |     (6 seconds in demo)          |
       |                                  |
       +-------> recovery detects    <----+
                 orphaned task
                      |
                      v
              task re-routed to broker
                      |
                      v
              Worker-2 picks it up
              and completes it
```

### Key Configuration (pyproject.toml)

| Setting | Demo Value | Default | Purpose |
|---------|-----------|---------|---------|
| `runner_considered_dead_after_minutes` | 0.1 (6s) | 10.0 | How long before a silent runner is considered dead |
| `recover_running_invocations_cron` | `* * * * *` | `*/15 * * * *` | How often recovery checks run |
| `atomic_service_interval_minutes` | 0.15 (9s) | 5.0 | Cycle length for global services (recovery, triggers) |

In production, these values are much higher to avoid false positives. For the demo they are lowered so recovery is visible within about a minute.

## Architecture

- **Backend:** SQLite (single file, no external services)
- **Runner:** ThreadRunner (one task at a time per worker process)
- **Recovery:** Heartbeat-based, runs as an atomic global service via cron trigger
