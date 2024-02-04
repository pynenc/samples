# Synchronous Unit Testing Example

## Introduction

The `sync_unit_testing` sample demonstrates how to perform synchronous unit testing on tasks defined with the `pynenc` library. By leveraging Pynenc's development mode, tasks can be executed synchronously, simplifying unit testing by avoiding the need for a running task processor.

## Important Disclaimer

While this example facilitates unit testing by running tasks synchronously, it bypasses Pynenc's distributed and asynchronous execution mechanisms. As such, this method should only be used for unit testing purposes, where task execution order and dependency management are not being tested. Be aware that this mode disables complex behaviors like automatic orchestration, executing all tasks sequentially and concurrently within the test environment itself.

## Requirements

- **Python:** Version 3.11 or higher.
- **Pynenc:** The `pynenc` library must be installed in your environment.

## Project Structure

- `tasks.py`: Contains the definition of a simple `add` task, showcasing how to write tasks intended for unit testing.
- `sample.py`: A demonstration script that executes the `add` task using a `ThreadRunner` to show typical task execution outside of testing.
- `test_add.py`: Includes unit tests for the `add` task, demonstrating how to enforce synchronous execution within tests.

## Running the Example

1. **Setup Environment:**
   Ensure that Python 3.11 and the Pynenc library are installed.

2. **Execute the Demonstration Script:**
   Run the `sample.py` script to see the `add` task executed in a threaded environment:
   ```bash
   python sample.py
   ```

3. **Run Unit Tests:**
   Execute the `test_add.py` script to run unit tests on the `add` task, ensuring tasks run synchronously during tests:
   ```bash
   python -m unittest test_add.py
   ```

## Understanding the Sample Script

- The `run_add_on_thread` function within `sample.py` demonstrates typical asynchronous task execution using a thread runner, contrasting with the synchronous execution used in testing.
- `test_add.py` contains two test classes that illustrate different methods for enforcing synchronous task execution during testing:
  - `TestAddTaskConf` directly sets the `dev_mode_force_sync_tasks` configuration to `True`.
  - `TestAddTaskEnviron` uses `unittest.mock.patch.dict` to temporarily set the `PYNENC__DEV_MODE_FORCE_SYNC_TASKS` environment variable to `True`.

## Conclusion

The `sync_unit_testing` sample provides an essential guide for writing and running unit tests for `pynenc` tasks, focusing on synchronous execution to simplify testing. It highlights the flexibility of Pynenc in adapting to different testing needs, allowing developers to efficiently test their task logic in isolation.
