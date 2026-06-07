"""Tiny CLI to fire named events into the trigger backend.

Usage::

    uv run python events.py feed_updated --source rss_live
    uv run python events.py feed_updated --source rss_live --count 8

Used by the README's two-terminal flow and by ``enqueue.py`` for the
event-driven scenarios. Producers stay quiet; the worker prints the reaction.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# Quiet the producer-side INFO chatter before importing tasks.
os.environ.setdefault("DEMO_LOG_LEVEL", "warning")

import tasks  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("event_code", help="Event code to fire (e.g. feed_updated)")
    parser.add_argument(
        "--payload",
        type=str,
        default=None,
        help="JSON object to use as the full payload (overrides --source/--count)",
    )
    parser.add_argument("--source", default=None, help="Shortcut: payload['source']")
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Shortcut: payload['count'] (only meaningful for feed_updated)",
    )
    args = parser.parse_args()

    if args.payload is not None:
        payload = json.loads(args.payload)
    else:
        payload = {}
        if args.source is not None:
            payload["source"] = args.source
        if args.count is not None:
            payload["count"] = args.count

    event_id = tasks.app.trigger.emit_event(args.event_code, payload=payload)
    print(f"emitted event_code={args.event_code} payload={payload} event_id={event_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
