"""Run one trigger-demo scenario and print what triggered.

Each scenario is one CS / distributed-systems concept from the README:

    A. polling_vs_reactive — manual polling loop vs. on_status trigger
    B. cron               — cron declaration (the schedule itself; no waiting)
    C. event_pubsub       — emit_event → ingest_feed → enrich_article fan-out
    D. pipeline           — chained on_status with argument filter
    E. compensation       — on_exception fires alert_editorial
    F. composite          — on_status AND on_result(count > threshold)
    all                   — A..F in order

Run with the worker already up::

    uv run pynenc --app tasks.app runner start         # in another terminal
    uv run python enqueue.py event_pubsub
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from collections.abc import Callable

# Quiet pynenc's producer-side INFO chatter before importing tasks.
os.environ.setdefault("DEMO_LOG_LEVEL", "warning")

import tasks  # noqa: E402
from pynenc.invocation.status import InvocationStatus  # noqa: E402

# How long to wait for trigger-driven reactions to land. Triggers are evaluated
REACTION_TIMEOUT = 12.0


def _count(task: object, statuses: list[InvocationStatus] | None = None) -> int:
    return tasks.app.orchestrator.count_invocations(task_id=task.task_id, statuses=statuses)


def _wait_for(predicate: Callable[[], bool], timeout: float = REACTION_TIMEOUT) -> bool:
    """Poll ``predicate`` until it returns True or the timeout elapses."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.25)
    return False


# --------------------------------------------------------------------------- #
# Scenarios
# --------------------------------------------------------------------------- #


def scenario_polling_vs_reactive() -> None:
    print("\n=== A. polling_vs_reactive ===")
    before_reactive = _count(tasks.reactive_tasks)
    target = tasks.poll_target()
    polling = tasks.polling_tasks(target)
    print(f"  Target invocation:   {target.invocation_id}")
    print(f"  Polling invocation:  {polling.invocation_id}")
    print("  Reactive invocation: created from poll_target SUCCESS")

    ok = _wait_for(lambda: polling.status.is_final() and _count(tasks.reactive_tasks) > before_reactive)
    print(
        f"  {'OK' if ok else 'TIMED OUT'}: polling_tasks observed completion;"
        f" reactive_tasks +{_count(tasks.reactive_tasks) - before_reactive}"
    )


def scenario_cron() -> None:
    print("\n=== B. cron ===")
    print("  Declared:  ingest_feed       on_cron('*/15 * * * *')")
    print("  Declared:  archive_old_content  on_cron('0 2 * * *')")
    print(
        "  No imperative scheduling code, no separate Beat process. The"
        " trigger backend evaluates these on every scheduler tick."
    )
    print(
        "  We do not wait for a real cron tick in this demo (15 min) — the"
        " event-driven path below shows the same task firing reactively."
    )


def scenario_event_pubsub() -> None:
    print("\n=== C. event_pubsub ===")
    before_ingest = _count(tasks.ingest_feed, [InvocationStatus.SUCCESS])
    before_enrich = _count(tasks.enrich_article, [InvocationStatus.SUCCESS])
    print("  Emitting event: feed_updated {source: 'rss_live', count: 3}")
    tasks.app.trigger.emit_event("feed_updated", payload={"source": "rss_live", "count": 3})
    # ingest_feed runs once and emits one event per article. Each matching
    # event creates its own enrich_article invocation; an event, not a caller,
    # drives the fan-out.
    ok = _wait_for(
        lambda: _count(tasks.ingest_feed, [InvocationStatus.SUCCESS]) > before_ingest
        and _count(tasks.enrich_article, [InvocationStatus.SUCCESS]) > before_enrich
    )
    after_ingest = _count(tasks.ingest_feed, [InvocationStatus.SUCCESS])
    after_enrich = _count(tasks.enrich_article, [InvocationStatus.SUCCESS])
    status = "OK" if ok else "TIMED OUT"
    print(
        f"  {status}: ingest_feed +{after_ingest - before_ingest},"
        f" enrich_article SUCCESS +{after_enrich - before_enrich}"
    )


def scenario_pipeline() -> None:
    print("\n=== D. pipeline ===")
    before_notify = _count(tasks.notify_subscribers)
    # Force a deterministic article that is breaking_news so the filter fires.
    print("  Emitting event: article_ingested {kind: 'breaking_news'}")
    tasks.app.trigger.emit_event(
        "article_ingested",
        payload={
            "article_id": "manual-breaking-01",
            "kind": "breaking_news",
            "source": "manual",
        },
    )
    ok = _wait_for(lambda: _count(tasks.notify_subscribers) > before_notify)
    delta = _count(tasks.notify_subscribers) - before_notify
    print(
        f"  {'OK' if ok else 'TIMED OUT'}: notify_subscribers +{delta}"
        " (filter call_arguments={'kind': 'breaking_news'})"
    )
    print("  Same pattern with a 'regular' kind would not fire notify_subscribers.")


def scenario_compensation() -> None:
    print("\n=== E. compensation ===")
    before_alert = _count(tasks.alert_editorial)
    print("  Emitting event: article_ingested {article_id: '*-bad'}")
    tasks.app.trigger.emit_event(
        "article_ingested",
        payload={"article_id": "manual-bad", "kind": "regular", "source": "manual"},
    )
    ok = _wait_for(lambda: _count(tasks.alert_editorial) > before_alert)
    delta = _count(tasks.alert_editorial) - before_alert
    print(
        f"  {'OK' if ok else 'TIMED OUT'}: alert_editorial +{delta} (on_exception(enrich_article, 'EnrichmentError'))"
    )


def scenario_composite() -> None:
    print("\n=== F. composite ===")
    threshold = tasks.DIGEST_THRESHOLD
    before_digest = _count(tasks.generate_digest)

    # Below threshold: AND fails, digest must NOT fire.
    small = threshold - 2
    print(f"  Emitting feed_updated count={small} (below threshold={threshold})")
    tasks.app.trigger.emit_event("feed_updated", payload={"source": "small_feed", "count": small})
    time.sleep(REACTION_TIMEOUT / 2)
    after_small = _count(tasks.generate_digest)
    print(f"  generate_digest delta={after_small - before_digest} (expected 0)")

    # Above threshold: AND satisfied, digest must fire.
    big = threshold + 3
    print(f"  Emitting feed_updated count={big} (above threshold={threshold})")
    tasks.app.trigger.emit_event("feed_updated", payload={"source": "big_feed", "count": big})
    ok = _wait_for(lambda: _count(tasks.generate_digest) > after_small)
    after_big = _count(tasks.generate_digest)
    delta = after_big - after_small
    print(f"  {'OK' if ok else 'TIMED OUT'}: generate_digest +{delta} (expected 1)")


SCENARIOS: dict[str, Callable[[], None]] = {
    "polling_vs_reactive": scenario_polling_vs_reactive,
    "cron": scenario_cron,
    "event_pubsub": scenario_event_pubsub,
    "pipeline": scenario_pipeline,
    "compensation": scenario_compensation,
    "composite": scenario_composite,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=[*SCENARIOS, "all"])
    args = parser.parse_args()

    keys = list(SCENARIOS) if args.scenario == "all" else [args.scenario]
    for key in keys:
        SCENARIOS[key]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
