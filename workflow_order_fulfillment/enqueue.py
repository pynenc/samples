"""Run order fulfillment workflow scenarios with an existing Pynenc runner."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Callable

os.environ.setdefault("DEMO_LOG_LEVEL", "warning")

import tasks  # noqa: E402


def base_order(
    order_id: str,
    *,
    payment_token: str = "tok_approved",
    simulate_transient_after_shipping: bool = False,
) -> tasks.Order:
    return tasks.Order(
        order_id=order_id,
        payment_token=payment_token,
        simulate_transient_after_shipping=simulate_transient_after_shipping,
    )


def print_summary(
    title: str,
    invocation_id: str,
    result: tasks.FulfillmentWorkflowResult,
) -> None:
    print(f"\n=== {title} ===")
    print(f"  invocation:  {invocation_id}")
    print(f"  workflow:    {result.workflow_id}")
    print(f"  order:       {result.order_id}")
    print(f"  status:      {result.status}")
    print(f"  attempts:    {result.attempt_count}")

    if result.tracking_number:
        print(f"  tracking:    {result.tracking_number}")
    if replayed := result.replayed_steps:
        print(f"  replayed:    {', '.join(replayed)}")
    if failure := result.workflow_data.get("failure_reason"):
        print(f"  reason:      {failure}")

    print("  workflow data:")
    print(json.dumps(result.workflow_data, indent=4, sort_keys=True))


def scenario_happy() -> None:
    order = base_order("ORD-HAPPY-1001")
    invocation = tasks.fulfill_order_workflow(order)
    result = invocation.result
    assert result.status == "fulfilled"
    assert result.attempt_count == 1
    print_summary("happy path", invocation.invocation_id, result)


def scenario_replay() -> None:
    order = base_order(
        "ORD-REPLAY-1002",
        simulate_transient_after_shipping=True,
    )
    invocation = tasks.fulfill_order_workflow(order)
    result = invocation.result
    assert result.status == "fulfilled"
    assert result.attempt_count == 2
    assert {"validate_order", "reserve_inventory", "charge_payment", "shipping_workflow"}.issubset(
        set(result.replayed_steps)
    )
    print_summary("durable replay after retry", invocation.invocation_id, result)


def scenario_payment_failure() -> None:
    order = base_order("ORD-DECLINE-1003", payment_token="decline")
    invocation = tasks.fulfill_order_workflow(order)
    result = invocation.result
    assert result.status == "payment_failed"
    assert result.release_id
    print_summary("payment failure with compensation", invocation.invocation_id, result)


SCENARIOS: dict[str, Callable[[], None]] = {
    "happy": scenario_happy,
    "replay": scenario_replay,
    "payment_failure": scenario_payment_failure,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=[*SCENARIOS, "all"])
    parser.add_argument(
        "--purge",
        action="store_true",
        help="Clear previous workflow state before running.",
    )
    args = parser.parse_args()

    if args.purge:
        tasks.app.purge()

    selected = SCENARIOS.values() if args.scenario == "all" else [SCENARIOS[args.scenario]]
    for scenario in selected:
        scenario()

    print("\nOpen Pynmon and inspect /workflows, /workflows/runs, and the invocation family tree.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
