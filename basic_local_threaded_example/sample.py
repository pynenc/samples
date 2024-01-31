import logging
import os
import threading

import tasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_add_on_thread() -> None:
    """Run add task on a thread"""

    def run_in_thread() -> None:
        tasks.app.conf.runner_cls = "ThreadRunner"
        tasks.app.runner.run()

    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()
    invocation = tasks.add(1, 2)
    logger.info(f"Result: {invocation.result}")
    tasks.app.runner.stop_runner_loop()
    thread.join()


def run_without_worker_add() -> None:
    """Run add task on the main thread"""
    results = []

    def run_task_with_timeout() -> None:
        logger.info("Running task with timeout")
        invocation = tasks.add(1, 2)
        results.append(invocation.result)
        logger.info(f"Result: {invocation.result}")

    thread = threading.Thread(target=run_task_with_timeout, daemon=True)
    thread.start()
    thread.join(timeout=2)
    if results != []:
        raise ValueError(f"Expected [], got {results}")
    logger.info(f"Task timeout, there was no worker to run the task")


def run_sync() -> None:
    """Modify the task to run synchronously"""
    tasks.app.conf.dev_mode_force_sync_tasks = True
    invocation = tasks.add(1, 2)
    logger.info(f"Result: {invocation.result}")


if __name__ == "__main__":
    run_add_on_thread()
    run_without_worker_add()
    run_sync()
