# Workflow order fulfillment demo

This sample is intentionally small. The order domain is only a frame for showing
Pynenc workflow behavior:

- a top-level `@app.workflow`
- child tasks executed through `wf.root.execute_task`
- deterministic workflow values from `wf.root.uuid()`, `wf.root.random()`, and
  `wf.root.utc_now()`
- a nested shipping sub-workflow
- retry and replay without duplicating completed child work
- a compensation task when payment is declined
- workflow data that is easy to inspect in Pynmon

The sample does not try to model real commerce. The business logic is tiny on
purpose so the workflow mechanics stay visible.

## Scenarios

| Scenario | Outcome | What it demonstrates |
| --- | --- | --- |
| `happy` | order is fulfilled | straight-through workflow and sub-workflow |
| `replay` | order is fulfilled after one controlled retry | completed child calls are reused |
| `payment_failure` | order stops after payment decline | compensation task releases the reservation |

The visible execution shape is:

```text
fulfill_order_workflow
  -> validate_order
  -> reserve_inventory
  -> charge_payment
  -> shipping_workflow
       -> choose_carrier
       -> create_shipping_label
  -> send_customer_confirmation
```

The payment failure path stops after `charge_payment` and runs
`release_inventory`.

## One-command run

This sample pins `pynenc[monitor]` to the TestPyPI release
`0.3.1rc120.dev211`, so `uv sync` exercises the published build instead of the
workspace checkout. The `tool.uv.sources` entry pins `pynenc` to the named
`testpypi` index, which is defined at `https://test.pypi.org/simple/`.

```bash
uv sync
uv run python sample.py
```

The script purges old state, starts a worker subprocess, runs all three
scenarios, prints a compact summary, and stops the worker.

## Run with Pynmon

Use three terminals from `samples/workflow_order_fulfillment/`:

```bash
# Terminal 1: worker
uv run pynenc --app tasks.app runner start

# Terminal 2: enqueue scenarios
uv run python enqueue.py happy --purge
uv run python enqueue.py replay
uv run python enqueue.py payment_failure

# Terminal 3: monitoring UI
uv run pynenc --app tasks.app monitor
```

Open <http://127.0.0.1:8000>.

Useful pages:

- `/workflows/` lists workflow types such as `fulfill_order_workflow` and
  `shipping_workflow`.
- `/workflows/runs` lists every workflow run.
- The invocation detail page shows retry history in the replay scenario.
- The family tree shows the parent workflow, child tasks, and nested shipping
  workflow.
- `/invocations?workflow_id=<workflow-id>` filters the invocation table to one
  workflow run.

## Why the replay scenario matters

The replay scenario raises `TransientFulfillmentError` after the shipping label
has been created. The main workflow retries once.

On the second attempt, these child calls are reached again:

```python
validation = fulfill_order_workflow.wf.root.execute_task(
    validate_order,
    order,
    validated_at,
).result

inventory = fulfill_order_workflow.wf.root.execute_task(
    reserve_inventory,
    order.order_id,
    order.item_count,
    reservation_id,
).result
```

Because the calls go through `wf.root.execute_task`, Pynenc returns the
previously recorded child invocations instead of creating a second validation,
reservation, payment, or shipment. The summary prints those reused steps as
`replayed_steps`.

## Architecture

- Backend: SQLite in `workflow_order_fulfillment.db`
- Runner: `ThreadRunner` with 10 threads
- External services: none
- Serializer: default Pynenc serializer
- Monitoring: built-in Pynmon through `pynenc monitor`
