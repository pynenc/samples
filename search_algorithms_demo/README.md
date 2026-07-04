# Search Algorithms Demo: Every Step Is a Task

This sample turns four familiar search algorithms into Pynenc task graphs:

- linear search
- binary search
- breadth-first search
- depth-first search

It is intentionally not a performance recipe. Searching nine integers does not
benefit from a broker, SQLite, serialization, and a pool of worker processes.
The small inputs make each algorithm's shape easy to inspect in Pynmon.

## What to Look For

| Algorithm | Pynmon shape |
| --- | --- |
| Linear search | A long chain, one comparison after another |
| Binary search | A much shorter chain as the interval halves |
| Breadth-first search | Wide waves of node-inspection tasks |
| Depth-first search | A narrow nested path with visible backtracking |

Every comparison or graph visit is a task. The artificial 120 ms delay makes
short invocations visible on the timeline.

## Runner Setup

The sample uses SQLite and `PersistentProcessRunner`. It deliberately creates
four more worker processes than the machine reports as logical CPUs:

```python
LOGICAL_CPUS = os.cpu_count() or 1
WORKER_PROCESSES = LOGICAL_CPUS + 4
```

That oversubscription gives Pynmon more runner lines and leaves slots available
when recursive tasks wait for child results. It is for this visualization, not
a production sizing recommendation.

## One-Command Run

```bash
cd search_algorithms_demo
uv sync
uv run python sample.py
```

The script purges old state, starts the runner, executes all four algorithms,
prints their results, and stops the runner.

## Run with Pynmon

Use three terminals for the useful version:

```bash
# Terminal 1: fixed process pool
uv run pynenc --app tasks.app runner start

# Terminal 2: run all algorithms or one at a time
uv run python enqueue.py all --purge
uv run python enqueue.py breadth_first

# Terminal 3: monitoring UI
uv run pynenc --app tasks.app monitor
```

Open <http://127.0.0.1:8000> and compare the invocation timeline and family
trees.

## A Fixed-Pool Boundary

`PersistentProcessRunner` workers remain occupied while a task waits for a
child invocation. A recursive task tree deeper than the available process pool
can therefore stall. These inputs are deliberately shallow, and the pool is
deliberately oversized, so the leaves always have room to run.
