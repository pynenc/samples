"""Pynenc tasks demonstrating the trigger system.

This file is the centrepiece of the sample. Each task carries a trigger
declaration that demonstrates a different distributed-systems pattern:

* ``ingest_feed``        — cron schedule + event subscription (declared as
                           two separate triggers; each keeps its own
                           argument provider).
* ``enrich_article``     — reacts to an event emitted by ``ingest_feed``.
* ``notify_subscribers`` — pipelines on ``enrich_article`` SUCCESS, filtered
                           by the original call arguments (only "breaking_news").
* ``alert_editorial``    — Saga-style compensation: triggers when
                           ``enrich_article`` raises ``EnrichmentError``.
* ``generate_digest``    — composite AND: ingest succeeded AND returned more
                           than the digest threshold.
* ``archive_old_content`` — pure cron scheduling, no caller needed.
* ``polling_tasks``       — actively polls another invocation's status.
* ``wait_result_tasks``   — waits through pynenc's invocation result API.
* ``reactive_tasks``      — reacts to that same invocation reaching SUCCESS.

The plain ``poll_target`` task gives both comparison paths the same work to
observe.

The shared pynenc configuration lives in ``pyproject.toml`` so Pynmon and the
CLI runner use the same backends and timing. This module uses
``PynencBuilder`` only to override the log level for producer scripts.
"""

from __future__ import annotations

import os
import random
import time
from typing import TYPE_CHECKING, Any

from pynenc import PynencBuilder
from pynenc.invocation.status import InvocationStatus
from pynenc.trigger.conditions.event import EventContext
from pynenc.trigger.conditions.exception import ExceptionContext
from pynenc.trigger.trigger_builder import TriggerBuilder

if TYPE_CHECKING:
    from pynenc.invocation import DistributedInvocation

# Producer scripts override this to keep their console clean.
LOG_LEVEL = os.environ.get("DEMO_LOG_LEVEL", "info")

app = PynencBuilder().logging_level(LOG_LEVEL).build()


# --------------------------------------------------------------------------- #
# Domain helpers — a tiny fake "article" universe.
# --------------------------------------------------------------------------- #

_KINDS = ("regular", "regular", "regular", "breaking_news")


def _make_articles(source: str, count: int) -> list[dict[str, str]]:
    """Generate fake article records for ``source``."""
    return [
        {
            "article_id": f"{source}-{i:02d}",
            "kind": random.choice(_KINDS),
            "source": source,
        }
        for i in range(count)
    ]


# --------------------------------------------------------------------------- #
# 1. ``ingest_feed`` — cron + event (scheduling + pub/sub).
# --------------------------------------------------------------------------- #


def _args_from_feed_event(ctx: EventContext) -> dict[str, Any]:
    """Map a ``feed_updated`` event payload to ingest_feed args."""
    return {
        "source": ctx.payload.get("source", "default"),
        "count": ctx.payload.get("count", 3),
    }


# Cron and event are both reasons to refresh the feed. Most frameworks make
# you wire each one separately; pynenc lets a task declare both. We attach
# them as two independent triggers — pynenc fires the task on either, and each
# trigger keeps its own argument provider (cron uses static defaults; event
# pulls args from its payload).
ingest_triggers = [
    TriggerBuilder()
    .on_cron("*/15 * * * *")  # every 15 minutes (declarative; not waited on in the demo)
    .with_args_static({"source": "scheduled", "count": 3}),
    TriggerBuilder().on_event("feed_updated").with_args_from_event(_args_from_feed_event),
]


@app.task(triggers=ingest_triggers)
def ingest_feed(source: str = "default", count: int = 3) -> dict[str, Any]:
    """Pull articles from ``source`` and emit one event per article.

    Returns a small summary so downstream triggers can filter on the count.
    Per-article fan-out is done by emitting ``article_ingested`` events,
    which is the pub/sub primitive ``enrich_article`` listens on.
    """
    ingest_feed.logger.info(f"ingest_feed(source={source!r}, count={count})")
    articles = _make_articles(source, count)
    for art in articles:
        app.trigger.emit_event("article_ingested", payload=art)
    return {"source": source, "count": len(articles)}


# --------------------------------------------------------------------------- #
# 2. ``enrich_article`` — reacts to per-article events (Observer / pub/sub).
# --------------------------------------------------------------------------- #


def _args_from_article_event(ctx: EventContext) -> dict[str, Any]:
    """Map an ``article_ingested`` event payload to enrich_article args."""
    return {"article_id": ctx.payload["article_id"], "kind": ctx.payload["kind"]}


class EnrichmentError(RuntimeError):
    """Domain failure used to drive the compensation trigger."""


@app.task(
    triggers=TriggerBuilder().on_event("article_ingested").with_args_from_event(_args_from_article_event),
)
def enrich_article(article_id: str, kind: str) -> dict[str, str]:
    """Enrich a single article. Articles with id ending in ``-bad`` fail."""
    enrich_article.logger.info(f"enrich_article({article_id!r}, kind={kind!r})")
    time.sleep(0.05)
    if article_id.endswith("-bad"):
        raise EnrichmentError(f"malformed payload for {article_id}")
    return {"article_id": article_id, "kind": kind, "status": "enriched"}


# --------------------------------------------------------------------------- #
# 3. ``notify_subscribers`` — pipeline + argument filter.
# --------------------------------------------------------------------------- #


def _args_from_enrich_status(ctx: Any) -> dict[str, Any]:
    """Pull the article_id from the upstream call arguments.

    ``ctx`` is a StatusContext; ``ctx.arguments.kwargs`` carries the args
    that ``enrich_article`` was called with.
    """
    return {"article_id": ctx.arguments.kwargs["article_id"]}


@app.task(
    triggers=TriggerBuilder()
    # ``call_arguments`` filters the upstream call: only fire when
    # enrich_article succeeded for a breaking_news article.
    .on_status(
        enrich_article,
        statuses=[InvocationStatus.SUCCESS],
        call_arguments={"kind": "breaking_news"},
    )
    .with_args_from_status(_args_from_enrich_status),
)
def notify_subscribers(article_id: str) -> str:
    """Notify subscribers about a freshly enriched breaking-news article."""
    notify_subscribers.logger.info(f"notify_subscribers({article_id!r})")
    time.sleep(0.05)
    return f"notified:{article_id}"


# --------------------------------------------------------------------------- #
# 4. ``alert_editorial`` — Saga-style compensation on ``EnrichmentError``.
# --------------------------------------------------------------------------- #


def _args_from_enrich_exception(ctx: ExceptionContext) -> dict[str, Any]:
    return {
        "article_id": ctx.arguments.kwargs.get("article_id", "?"),
        "error": f"{ctx.exception_type}: {ctx.exception_message}",
    }


@app.task(
    triggers=TriggerBuilder()
    .on_exception(enrich_article, exception_types="EnrichmentError")
    .with_args_from_exception(_args_from_enrich_exception),
)
def alert_editorial(article_id: str, error: str) -> str:
    """Compensating action when an article cannot be enriched."""
    alert_editorial.logger.info(f"alert_editorial({article_id!r}, error={error!r})")
    return f"alerted:{article_id}"


# --------------------------------------------------------------------------- #
# 5. ``generate_digest`` — composite AND with a result filter.
# --------------------------------------------------------------------------- #

DIGEST_THRESHOLD = 5


def _digest_threshold_filter(result: dict[str, Any]) -> bool:
    """Pass when the ingest produced more than DIGEST_THRESHOLD articles."""
    return bool(result.get("count", 0) > DIGEST_THRESHOLD)


@app.task(
    triggers=TriggerBuilder()
    .on_status(ingest_feed, statuses=[InvocationStatus.SUCCESS])
    .on_result(ingest_feed, filter_result=_digest_threshold_filter)
    .with_logic("and"),
)
def generate_digest() -> str:
    """Generated only when an ingest succeeded AND it brought enough articles."""
    generate_digest.logger.info("generate_digest()")
    return "digest_generated"


# --------------------------------------------------------------------------- #
# 6. ``archive_old_content`` — pure cron, no caller required.
# --------------------------------------------------------------------------- #


@app.task(triggers=TriggerBuilder().on_cron("0 2 * * *"))
def archive_old_content() -> str:
    """Runs at 02:00 every day. Declared, never explicitly invoked."""
    archive_old_content.logger.info("archive_old_content()")
    return "archived"


# --------------------------------------------------------------------------- #
# 7. Polling vs. reactive — two ways to observe the same target.
# --------------------------------------------------------------------------- #

POLL_INTERVAL_SECONDS = 0.3
TARGET_RUN_SECONDS = 0.2


@app.task
def poll_target() -> str:
    """A short task observed by both comparison paths."""
    time.sleep(TARGET_RUN_SECONDS)
    return "done"


@app.task
def polling_tasks(target: DistributedInvocation) -> str:
    """Poll durable status until the target succeeds."""
    _ = target.result
    return "observed"


@app.task(
    triggers=TriggerBuilder().on_status(poll_target, statuses=[InvocationStatus.SUCCESS]),
)
def reactive_tasks() -> str:
    """Run after pynenc processes the target's SUCCESS condition."""
    return "reacted"
