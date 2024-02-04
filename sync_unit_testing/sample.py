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


if __name__ == "__main__":
    run_add_on_thread()
