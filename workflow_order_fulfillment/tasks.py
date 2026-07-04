"""Small order workflow demo for Pynenc workflows and Pynmon."""

from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from typing import Any

from pynenc import PynencBuilder

STEP_DELAY_SECONDS = 0.15
LOG_LEVEL = os.environ.get("DEMO_LOG_LEVEL", "info")

app = (
    PynencBuilder()
    .app_id("workflow_order_fulfillment")
    .sqlite("workflow_order_fulfillment.db")
    .thread_runner(min_threads=1, max_threads=10)
    .runner_tuning(
        runner_loop_sleep_time_sec=0.02,
        invocation_wait_results_sleep_time_sec=0.02,
    )
    .logging_stream("stdout")
    .logging_level(LOG_LEVEL)
    .logging_colors(False)
    .argument_print_mode("truncated", truncate_length=80)
    .build()
)


class TransientFulfillmentError(RuntimeError):
    """Raised once by the replay scenario to force a workflow retry."""


@dataclass(frozen=True)
class Order:
    order_id: str
    customer_email: str = "buyer@example.com"
    item_count: int = 2
    payment_token: str = "tok_approved"
    simulate_transient_after_shipping: bool = False


@dataclass(frozen=True)
class ValidationResult:
    accepted: bool
    reason: str | None = None


@dataclass(frozen=True)
class InventoryResult:
    reserved: bool
    reservation_id: str
    reason: str | None = None


@dataclass(frozen=True)
class PaymentResult:
    approved: bool
    payment_id: str
    reason: str | None = None


@dataclass(frozen=True)
class ShippingResult:
    shipment_id: str
    tracking_number: str
    carrier: str


@dataclass(frozen=True)
class ReleaseResult:
    release_id: str
    reservation_id: str
    reason: str


@dataclass(frozen=True)
class FulfillmentWorkflowResult:
    workflow_id: str
    order_id: str
    status: str
    attempt_count: int
    workflow_data: dict[str, Any]
    tracking_number: str | None = None
    failure_reason: str | None = None
    reservation_id: str | None = None
    payment_id: str | None = None
    release_id: str | None = None
    confirmation_id: str | None = None
    replayed_steps: tuple[str, ...] = ()


AVAILABLE_STOCK = 3


def _stable_id(prefix: str, namespace: str, *parts: Any) -> str:
    raw = "|".join(str(part) for part in (namespace, *parts))
    digest = hashlib.sha1(raw.encode()).hexdigest()[:8]
    return f"{prefix}-{digest}"


def _root_uuid() -> str:
    return str(fulfill_order_workflow.wf.root.uuid())


def _root_now() -> str:
    return fulfill_order_workflow.wf.root.utc_now().isoformat()


def _workflow_data_snapshot() -> dict[str, Any]:
    keys = [
        "order_id",
        "status",
        "attempt_count",
        "started_at",
        "validated_at",
        "reservation_id",
        "payment_id",
        "shipment_id",
        "tracking_number",
        "confirmation_id",
        "inventory_release_id",
        "failure_reason",
        "transient_probe_raised",
    ]
    return {key: fulfill_order_workflow.wf.get_data(key) for key in keys}


@app.task
def validate_order(order: Order, validated_at: str) -> ValidationResult:
    """Accept only orders that make sense for the workflow demo."""
    time.sleep(STEP_DELAY_SECONDS)
    validate_order.wf.set_data("validated_at", validated_at)

    if not order.order_id:
        return ValidationResult(False, "missing_order_id")
    if order.item_count <= 0:
        return ValidationResult(False, "empty_order")
    if not order.customer_email:
        return ValidationResult(False, "missing_customer_email")
    return ValidationResult(True)


@app.task
def reserve_inventory(
    order_id: str,
    item_count: int,
    reservation_id: str,
) -> InventoryResult:
    """Reserve a tiny in-memory stock quantity."""
    time.sleep(STEP_DELAY_SECONDS)
    if item_count > AVAILABLE_STOCK:
        return InventoryResult(False, reservation_id, "not_enough_stock")

    reserve_inventory.wf.set_data("reservation_id", reservation_id)
    reserve_inventory.logger.info(f"Reserved {item_count} items for {order_id}")
    return InventoryResult(True, reservation_id)


@app.task
def charge_payment(
    order_id: str,
    payment_token: str,
    payment_id: str,
) -> PaymentResult:
    """Approve every token except the demo decline token."""
    time.sleep(STEP_DELAY_SECONDS)
    if payment_token == "decline":
        return PaymentResult(False, payment_id, "card_declined")

    charge_payment.wf.set_data("payment_id", payment_id)
    charge_payment.logger.info(f"Payment approved for {order_id}")
    return PaymentResult(True, payment_id)


@app.task
def choose_carrier(order_id: str) -> str:
    """Tiny step task so the shipping sub-workflow has visible children."""
    time.sleep(STEP_DELAY_SECONDS)
    choose_carrier.logger.info(f"Carrier selected for {order_id}")
    return "SwissPost"


@app.task
def create_shipping_label(
    order_id: str,
    carrier: str,
    shipment_id: str,
    tracking_number: str,
) -> ShippingResult:
    """Create the label from deterministic values supplied by the workflow."""
    time.sleep(STEP_DELAY_SECONDS)
    create_shipping_label.logger.info(f"Shipping label created for {order_id}")
    return ShippingResult(shipment_id, tracking_number, carrier)


@app.workflow
def shipping_workflow(
    order_id: str,
    reservation_id: str,
    payment_id: str,
) -> ShippingResult:
    """Sub-workflow that makes nested workflow structure visible in Pynmon."""
    shipping_workflow.wf.set_data("order_id", order_id)
    shipping_workflow.wf.set_data("reservation_id", reservation_id)
    shipping_workflow.wf.set_data("payment_id", payment_id)
    shipping_workflow.wf.set_data("status", "shipping_started")

    carrier_invocation = shipping_workflow.wf.root.execute_task(
        choose_carrier,
        order_id,
    )
    carrier: str = carrier_invocation.result
    shipping_workflow.wf.set_data("carrier", carrier)

    shipment_id = _stable_id(
        "SHP",
        "shipment",
        order_id,
        carrier,
        shipping_workflow.wf.root.uuid(),
    )
    tracking_number = f"{carrier[:3].upper()}-{int(shipping_workflow.wf.root.random() * 1_000_000):06d}"
    label_invocation = shipping_workflow.wf.root.execute_task(
        create_shipping_label,
        order_id,
        carrier,
        shipment_id,
        tracking_number,
    )
    shipment: ShippingResult = label_invocation.result

    shipping_workflow.wf.set_data("status", "shipping_label_created")
    shipping_workflow.wf.set_data("shipment_id", shipment.shipment_id)
    shipping_workflow.wf.set_data("tracking_number", shipment.tracking_number)
    return shipment


@app.task
def send_customer_confirmation(
    order_id: str,
    customer_email: str,
    tracking_number: str,
    confirmation_id: str,
) -> str:
    """Send the final customer notification."""
    time.sleep(STEP_DELAY_SECONDS)
    send_customer_confirmation.wf.set_data("confirmation_id", confirmation_id)
    send_customer_confirmation.logger.info(f"Confirmation sent for {order_id} to {customer_email}: {tracking_number}")
    return confirmation_id


@app.task
def release_inventory(
    reservation_id: str,
    release_id: str,
    reason: str,
) -> ReleaseResult:
    """Compensating task used when a later business step fails."""
    time.sleep(STEP_DELAY_SECONDS)
    release_inventory.wf.set_data("inventory_release_id", release_id)
    return ReleaseResult(release_id, reservation_id, reason)


@app.workflow(retry_for=(TransientFulfillmentError,), max_retries=1)
def fulfill_order_workflow(order: Order) -> FulfillmentWorkflowResult:
    """Coordinate child tasks, replay, compensation, and a sub-workflow."""
    workflow_id = str(fulfill_order_workflow.wf.identity.workflow_id)
    attempt_count = int(fulfill_order_workflow.wf.get_data("attempt_count", 0)) + 1
    replayed_steps: list[str] = []

    fulfill_order_workflow.wf.set_data("attempt_count", attempt_count)
    fulfill_order_workflow.wf.set_data("order_id", order.order_id)
    fulfill_order_workflow.wf.set_data("status", "started")

    started_at_candidate = _root_now()
    started_at = fulfill_order_workflow.wf.get_data("started_at")
    if started_at is None:
        fulfill_order_workflow.wf.set_data("started_at", started_at_candidate)

    def execute_step(step: str, task: Any, *args: Any) -> Any:
        invocation = fulfill_order_workflow.wf.root.execute_task(task, *args)
        invocation_id = str(invocation.invocation_id)
        previous = fulfill_order_workflow.wf.get_data(f"{step}_invocation_id")
        fulfill_order_workflow.wf.set_data(f"{step}_invocation_id", invocation_id)
        if previous == invocation_id:
            replayed_steps.append(step)
        return invocation.result

    validation: ValidationResult = execute_step(
        "validate_order",
        validate_order,
        order,
        _root_now(),
    )
    if not validation.accepted:
        fulfill_order_workflow.wf.set_data("status", "validation_failed")
        fulfill_order_workflow.wf.set_data("failure_reason", validation.reason)
        return FulfillmentWorkflowResult(
            workflow_id=workflow_id,
            order_id=order.order_id,
            status="validation_failed",
            attempt_count=attempt_count,
            failure_reason=validation.reason,
            workflow_data=_workflow_data_snapshot(),
        )

    reservation_id = _stable_id("RSV", "reservation", order.order_id, _root_uuid())
    inventory: InventoryResult = execute_step(
        "reserve_inventory",
        reserve_inventory,
        order.order_id,
        order.item_count,
        reservation_id,
    )
    if not inventory.reserved:
        fulfill_order_workflow.wf.set_data("status", "inventory_failed")
        fulfill_order_workflow.wf.set_data("failure_reason", inventory.reason)
        return FulfillmentWorkflowResult(
            workflow_id=workflow_id,
            order_id=order.order_id,
            status="inventory_failed",
            attempt_count=attempt_count,
            failure_reason=inventory.reason,
            reservation_id=inventory.reservation_id,
            workflow_data=_workflow_data_snapshot(),
        )

    payment_id = _stable_id("PAY", "payment", order.order_id, _root_uuid())
    payment: PaymentResult = execute_step(
        "charge_payment",
        charge_payment,
        order.order_id,
        order.payment_token,
        payment_id,
    )
    if not payment.approved:
        release_id = _stable_id("REL", "release", order.order_id, inventory.reservation_id)
        release: ReleaseResult = execute_step(
            "release_inventory",
            release_inventory,
            inventory.reservation_id,
            release_id,
            "payment_declined",
        )
        fulfill_order_workflow.wf.set_data("status", "payment_failed")
        fulfill_order_workflow.wf.set_data("failure_reason", payment.reason)
        return FulfillmentWorkflowResult(
            workflow_id=workflow_id,
            order_id=order.order_id,
            status="payment_failed",
            attempt_count=attempt_count,
            failure_reason=payment.reason,
            reservation_id=inventory.reservation_id,
            payment_id=payment.payment_id,
            release_id=release.release_id,
            workflow_data=_workflow_data_snapshot(),
        )

    shipment: ShippingResult = execute_step(
        "shipping_workflow",
        shipping_workflow,
        order.order_id,
        inventory.reservation_id,
        payment.payment_id,
    )
    fulfill_order_workflow.wf.set_data("shipment_id", shipment.shipment_id)
    fulfill_order_workflow.wf.set_data("tracking_number", shipment.tracking_number)
    fulfill_order_workflow.wf.set_data("status", "shipping_label_created")

    if order.simulate_transient_after_shipping and not fulfill_order_workflow.wf.get_data(
        "transient_probe_raised",
        False,
    ):
        fulfill_order_workflow.wf.set_data("transient_probe_raised", True)
        fulfill_order_workflow.wf.set_data("status", "retrying_after_transient")
        raise TransientFulfillmentError("controlled transient failure after shipment")

    confirmation_id = _stable_id("CNF", "confirmation", order.order_id, _root_uuid())
    confirmation: str = execute_step(
        "send_customer_confirmation",
        send_customer_confirmation,
        order.order_id,
        order.customer_email,
        shipment.tracking_number,
        confirmation_id,
    )

    fulfill_order_workflow.wf.set_data("status", "fulfilled")
    fulfill_order_workflow.wf.set_data("completed_at", _root_now())
    return FulfillmentWorkflowResult(
        workflow_id=workflow_id,
        order_id=order.order_id,
        status="fulfilled",
        attempt_count=attempt_count,
        tracking_number=shipment.tracking_number,
        reservation_id=inventory.reservation_id,
        payment_id=payment.payment_id,
        confirmation_id=confirmation,
        replayed_steps=tuple(replayed_steps),
        workflow_data=_workflow_data_snapshot(),
    )
