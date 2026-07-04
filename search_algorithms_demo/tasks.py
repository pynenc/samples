"""Classic search algorithms where every comparison or node visit is a task."""

from __future__ import annotations

import os
import time
from typing import TypedDict

from pynenc import PynencBuilder

LOGICAL_CPUS = os.cpu_count() or 1
WORKER_PROCESSES = LOGICAL_CPUS + 4
STEP_DELAY_SECONDS = 0.12

app = (
    PynencBuilder()
    .app_id("search_algorithms_demo")
    .sqlite("search_algorithms_demo.db")
    .persistent_process_runner(num_processes=WORKER_PROCESSES)
    .runner_tuning(
        runner_loop_sleep_time_sec=0.01,
        invocation_wait_results_sleep_time_sec=0.01,
    )
    .logging_stream("stdout")
    .logging_level(os.environ.get("DEMO_LOG_LEVEL", "info"))
    .logging_colors(False)
    .argument_print_mode("truncated", truncate_length=56)
    .build()
)


class BreadthFirstInspection(TypedDict):
    path: list[str]
    matched: bool
    children: list[str]


@app.task
def linear_search(values: list[int], target: int, index: int = 0) -> int | None:
    """Check one list position, then delegate the next position to another task."""
    time.sleep(STEP_DELAY_SECONDS)
    if index >= len(values):
        linear_search.logger.info("Linear search exhausted the list")
        return None

    value = values[index]
    linear_search.logger.info(f"Linear search index={index}, value={value}, target={target}")
    if value == target:
        return index
    return linear_search(values, target, index + 1).result


@app.task
def binary_search(
    values: list[int],
    target: int,
    low: int,
    high: int,
) -> int | None:
    """Check one midpoint, then delegate the remaining half to another task."""
    time.sleep(STEP_DELAY_SECONDS)
    if low > high:
        binary_search.logger.info("Binary search interval is empty")
        return None

    middle = (low + high) // 2
    value = values[middle]
    binary_search.logger.info(f"Binary search low={low}, high={high}, middle={middle}, value={value}")
    if value == target:
        return middle
    if value < target:
        return binary_search(values, target, middle + 1, high).result
    return binary_search(values, target, low, middle - 1).result


@app.task
def inspect_breadth_first_node(
    graph: dict[str, list[str]],
    node: str,
    target: str,
    path: list[str],
) -> BreadthFirstInspection:
    """Inspect one node in the current breadth-first frontier."""
    time.sleep(STEP_DELAY_SECONDS)
    inspect_breadth_first_node.logger.info(f"Breadth-first visit node={node}, target={target}")
    return {
        "path": path,
        "matched": node == target,
        "children": graph.get(node, []),
    }


@app.task
def breadth_first_search(
    graph: dict[str, list[str]],
    start: str,
    target: str,
) -> list[str] | None:
    """Search one graph level at a time, distributing every node inspection."""
    frontier = [[start]]
    visited = {start}

    while frontier:
        inspections = inspect_breadth_first_node.parallelize(
            [
                {
                    "graph": graph,
                    "node": path[-1],
                    "target": target,
                    "path": path,
                }
                for path in frontier
            ]
        )
        level_results = list(inspections.results)

        for inspection in level_results:
            if inspection["matched"]:
                return inspection["path"]

        next_frontier: list[list[str]] = []
        for inspection in level_results:
            for child in inspection["children"]:
                if child not in visited:
                    visited.add(child)
                    next_frontier.append([*inspection["path"], child])
        frontier = next_frontier

    return None


@app.task
def depth_first_search(
    graph: dict[str, list[str]],
    node: str,
    target: str,
    path: list[str] | None = None,
    visited: list[str] | None = None,
) -> list[str] | None:
    """Visit one node, then recursively delegate each branch to another task."""
    current_path = [*(path or []), node]
    current_visited = [*(visited or []), node]
    time.sleep(STEP_DELAY_SECONDS)
    depth_first_search.logger.info(f"Depth-first visit node={node}, target={target}")

    if node == target:
        return current_path

    for child in graph.get(node, []):
        if child in current_visited:
            continue
        result = depth_first_search(
            graph,
            child,
            target,
            current_path,
            current_visited,
        ).result
        if result is not None:
            return result
    return None
