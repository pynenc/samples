import logging
import threading
from unittest.mock import patch

import tasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_fibonnaci_in_a_thread() -> None:
    """Demonstrates that the runner will iddle and resume task that depends in others"""

    # start a runner
    def run_in_thread() -> None:
        tasks.app.conf.runner_cls = "ThreadRunner"
        tasks.app.runner.run()

    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()

    # trigger fibonnaci task
    invocation = tasks.fibonacci(3)
    logger.info(f"Result: {invocation.result}")

    # stop the runner
    tasks.app.runner.stop_runner_loop()
    thread.join()


if __name__ == "__main__":
    # Run with environment variable `PYNENC__LOGGING_LEVEL=DEBUG` to observe the runner pausing and resuming tasks
    # PYNENC__LOGGING_LEVEL=DEBUG python sample.py
    run_fibonnaci_in_a_thread()
