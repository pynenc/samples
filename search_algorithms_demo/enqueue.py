"""Run one distributed search scenario with an existing Pynenc runner."""

from __future__ import annotations

import argparse
import os
from collections.abc import Callable

os.environ.setdefault("DEMO_LOG_LEVEL", "warning")

import tasks  # noqa: E402

LINEAR_VALUES = [17, 4, 9, 31, 8, 12, 5, 42, 23]
BINARY_VALUES = list(range(1, 32))
GRAPH = {
    "A": ["B", "C", "D"],
    "B": ["E", "F"],
    "C": ["G", "H"],
    "D": ["I", "J"],
    "E": ["K", "L"],
    "F": [],
    "G": [],
    "H": [],
    "I": [],
    "J": [],
    "K": [],
    "L": [],
}


def scenario_linear() -> None:
    print("\n=== 1. Linear search ===")
    invocation = tasks.linear_search(LINEAR_VALUES, 42)
    result = invocation.result
    assert result == 7
    print(f"  invocation: {invocation.invocation_id}")
    print(f"  found 42 at index {result}")


def scenario_binary() -> None:
    print("\n=== 2. Binary search ===")
    invocation = tasks.binary_search(
        BINARY_VALUES,
        target=26,
        low=0,
        high=len(BINARY_VALUES) - 1,
    )
    result = invocation.result
    assert result == 25
    print(f"  invocation: {invocation.invocation_id}")
    print(f"  found 26 at index {result}")


def scenario_breadth_first() -> None:
    print("\n=== 3. Breadth-first search ===")
    invocation = tasks.breadth_first_search(GRAPH, start="A", target="H")
    result = invocation.result
    assert result == ["A", "C", "H"]
    print(f"  invocation: {invocation.invocation_id}")
    print(f"  path: {' -> '.join(result)}")


def scenario_depth_first() -> None:
    print("\n=== 4. Depth-first search ===")
    invocation = tasks.depth_first_search(GRAPH, node="A", target="H")
    result = invocation.result
    assert result == ["A", "C", "H"]
    print(f"  invocation: {invocation.invocation_id}")
    print(f"  path: {' -> '.join(result)}")


SCENARIOS: dict[str, Callable[[], None]] = {
    "linear": scenario_linear,
    "binary": scenario_binary,
    "breadth_first": scenario_breadth_first,
    "depth_first": scenario_depth_first,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=[*SCENARIOS, "all"])
    parser.add_argument(
        "--purge",
        action="store_true",
        help="Clear previous invocations before running the scenario.",
    )
    args = parser.parse_args()

    if args.purge:
        tasks.app.purge()

    selected = SCENARIOS.values() if args.scenario == "all" else [SCENARIOS[args.scenario]]
    for scenario in selected:
        scenario()

    print("\nAll selected searches completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
