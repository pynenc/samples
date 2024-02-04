import os
import threading
import unittest
from unittest.mock import patch

import tasks


class TestAddTaskConf(unittest.TestCase):
    """Test suite for add task"""

    def setUp(self) -> None:
        # Configure Pynenc to use in-memory components and thread runner
        tasks.app.conf.dev_mode_force_sync_tasks = False
        tasks.app.conf.orchestrator_cls = "MemOrchestrator"
        tasks.app.conf.broker_cls = "MemBroker"
        tasks.app.conf.state_backend_cls = "MemStateBackend"
        tasks.app.conf.runner_cls = "ThreadRunner"

        # Start a runner thread
        self.thread = threading.Thread(target=self.run_in_thread, daemon=True)
        self.thread.start()

    def run_in_thread(self) -> None:
        tasks.app.runner.run()

    def tearDown(self) -> None:
        """Cleanup after tests."""
        # Stop the runner loop
        tasks.app.runner.stop_runner_loop()
        self.thread.join()

    def test_add(self) -> None:
        """Test add task"""
        invocation = tasks.add(1, 2)
        assert invocation.result == 3


class TestAddTaskEnviron(unittest.TestCase):
    """Test suite for add task"""

    def setUp(self) -> None:
        # Patch the environment variable
        self.patcher = patch.dict(
            os.environ,
            {
                "PYNENC__DEV_MODE_FORCE_SYNC_TASKS": "False",
                "PYNENC__RUNNER_CLS": "ThreadRunner",
                "PYNENC__ORCHESTRATOR_CLS": "MemOrchestrator",
                "PYNENC__BROKER_CLS": "MemBroker",
                "PYNENC__STATE_BACKEND_CLS": "MemStateBackend",
            },
        )
        self.patcher.start()
        # Start a runner thread
        self.thread = threading.Thread(target=self.run_in_thread, daemon=True)
        self.thread.start()

    def run_in_thread(self) -> None:
        tasks.app.runner.run()

    def tearDown(self) -> None:
        """Cleanup after tests."""
        # Stop the runner loop
        tasks.app.runner.stop_runner_loop()
        self.thread.join()
        # Stop the patcher to remove the environment variable patch
        self.patcher.stop()

    def test_add(self) -> None:
        """Test add task"""
        invocation = tasks.add(1, 2)
        self.assertEqual(invocation.result, 3)


if __name__ == "__main__":
    unittest.main()
