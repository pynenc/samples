import logging
import os
import threading

import tasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_without_concurrency_control() -> None:
    """
    Demonstrate that without concurrency control each call will be routed
    and therefore trigger a new run of the decorated function
    (generating a new invocation id)
    """
    # we just trigger the task 10 times without any runner to check that each call will generate a new invocation id
    invocations = [tasks.get_own_invocation_id() for _ in range(10)]
    if len(set(invocations)) != len(invocations):
        raise ValueError(f"Expected 10 unique invocations, got {invocations}")
    logger.info(f"Invocation ids: " + ", ".join(i.invocation_id for i in invocations))


def run_with_registration_concurrency_control() -> None:
    """
    Demonstrate that with concurrency control enabled at Task level `ConcurrencyControlType.TASK`,
    only one task will be routed
    so all these call will only trigger one run of the decorated function
    (generating only one invocation id)

    **Note:**
        It will return 2 different invocation objects that share the same id.
        The initial `DistributedInvocation` and then `ReusedInvocation`(s) with the same id.
    """
    # in this case ConcurrencyControlType.TASK will only allow one registered (routed) invocation at a time for the task
    invocations = [
        tasks.get_own_invocation_id_registration_concurrency() for _ in range(3)
    ]
    invocation_ids = {i.invocation_id for i in invocations}
    if len(invocation_ids) != 1:
        raise ValueError(f"Expected an unique invocation_id, got {invocations}")
    logger.info(f"Unique invocation_id: {set(invocation_ids)}")


def any_run_in_parallel(results: list[tasks.SleepResult]) -> bool:
    """Check if any tasks in the list ran in parallel (overlapping times)."""
    sorted_results = sorted(results, key=lambda x: x.start)
    for i in range(1, len(sorted_results)):
        if sorted_results[i].start < sorted_results[i - 1].end:
            print(f"Overlap: {sorted_results[i - 1]} and {sorted_results[i]}")
            return True  # Found an overlap, tasks ran in parallel
    return False  # No overlap found, tasks did not run in parallel


def run_with_running_concurrency_control() -> None:
    """Demonstrate that the concurrency control will prevent running multiple tasks at the same time"""
    # first purge any invocation pending from previous runs
    # warning! purgue will remove any persistent data from the application
    tasks.app.purge()

    # start a runner
    def run_in_thread() -> None:
        tasks.app.conf.runner_cls = "ThreadRunner"
        tasks.app.runner.run()

    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()

    # check that without control runs in parallel
    no_control_invocations = [
        tasks.sleep_without_running_concurrency(0.1) for _ in range(10)
    ]
    no_control_results = [i.result for i in no_control_invocations]
    if not any_run_in_parallel(no_control_results):
        raise ValueError(f"Expected parallel execution, got {no_control_results}")

    # check that with control does not run in parallel
    controlled_invocations = [
        tasks.sleep_with_running_concurrency(0.1) for _ in range(10)
    ]
    controlled_results = [i.result for i in controlled_invocations]
    if any_run_in_parallel(controlled_results):
        raise ValueError(f"Expected sequential execution, got {controlled_results}")

    # stop the runner
    tasks.app.runner.stop_runner_loop()
    thread.join()


if __name__ == "__main__":
    run_without_concurrency_control()
    run_with_registration_concurrency_control()
    run_with_running_concurrency_control()
