import os
import unittest
from unittest.mock import patch

import tasks


class TestAddTaskConf(unittest.TestCase):
    """Test suite for add task"""

    def setUp(self) -> None:
        tasks.app.conf.dev_mode_force_sync_tasks = True

    def test_add(self) -> None:
        """Test add task"""
        invocation = tasks.add(1, 2)
        assert invocation.result == 3


class TestAddTaskEnviron(unittest.TestCase):
    """Test suite for add task"""

    def setUp(self) -> None:
        self.patcher = patch.dict(
            os.environ, {"PYNENC__DEV_MODE_FORCE_SYNC_TASKS": "True"}
        )
        self.patcher.start()

    def tearDown(self) -> None:
        self.patcher.stop()

    def test_add(self) -> None:
        """Test add task"""
        invocation = tasks.add(1, 2)
        self.assertEqual(invocation.result, 3)


if __name__ == "__main__":
    unittest.main()
