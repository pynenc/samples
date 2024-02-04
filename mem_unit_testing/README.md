# Synchronous Unit Testing with Thread Runner

## Introduction

The `sync_unit_testing` sample showcases a testing strategy for Pynenc tasks that leverages synchronous execution in a controlled, in-memory environment. This approach is particularly useful for unit testing, where the asynchronous and distributed nature of tasks can introduce complexity and unpredictability.

## Important Disclaimer

This testing approach configures Pynenc to use in-memory components and a thread runner, allowing tasks to execute within the same process as the test runner. While this setup closely mimics a real execution environment, it bypasses the distributed nature of Pynenc. It's intended solely for testing purposes where task interactions and state do not need to persist beyond the test's scope.

## Requirements

- **Python:** Version 3.11 or higher.
- **Pynenc:** The `pynenc` library must be installed in your test environment.

## Project Structure

- `tasks.py`: Defines the `add` task to demonstrate how tasks can be unit tested.
- `test_add.py`: Contains unit tests for the `add` task, highlighting two approaches to initiate synchronous execution within tests.

## Testing Setup

The unit tests use two primary methods to achieve synchronous execution:

1. **Configuration-based Synchronous Mode:** Directly sets the Pynenc configuration to use in-memory components and a thread runner, bypassing the need for external task processing infrastructure.
2. **Environment Variable Patching:** Uses `unittest.mock.patch.dict` to modify environment variables, forcing Pynenc into a synchronous mode suitable for testing.

## Running the Tests

To execute the tests and validate the `add` task behavior:

"""bash
python -m unittest test_add.py
"""

This command runs all tests defined in `test_add.py`, demonstrating the effectiveness of synchronous unit testing for tasks.

## Example Test Case

"""python
import os
import threading
import unittest
from unittest.mock import patch

import tasks

class TestAddTaskConf(unittest.TestCase):
    def setUp(self):
        # Configure Pynenc for synchronous execution
        tasks.app.conf.dev_mode_force_sync_tasks = False
        tasks.app.conf.orchestrator_cls = "MemOrchestrator"
        tasks.app.conf.broker_cls = "MemBroker"
        tasks.app.conf.state_backend_cls = "MemStateBackend"
        tasks.app.conf.runner_cls = "ThreadRunner"

        # Initialize the runner in a separate thread
        self.thread = threading.Thread(target=self.run_in_thread, daemon=True)
        self.thread.start()

    def run_in_thread(self):
        tasks.app.runner.run()

    def tearDown(self):
        # Ensure clean test teardown
        tasks.app.runner.stop_runner_loop()
        self.thread.join()

    def test_add(self):
        # Perform the test
        invocation = tasks.add(1, 2)
        self.assertEqual(invocation.result, 3)
"""

## Conclusion

The `sync_unit_testing` sample provides a clear and straightforward approach to unit testing Pynenc tasks. By leveraging Pynenc's configurable architecture and Python's standard testing framework, developers can write concise and predictable tests for their task logic, ensuring reliable behavior across different environments.
