# Concurrency Control Example

## Introduction
The `concurrency_control` sample focus on concurrency control mechanisms. This example illustrates how to use concurrency control to manage task registration, and managing running tasks.

## Important Disclaimer
This example explores `ConcurrencyControlType` configurations in `pynenc`, including `DISABLED` and `TASK` levels for both task registration and running tasks. It's designed to show how `pynenc` can be configured to handle tasks in different concurrency scenarios. Note that while these features are powerful, they should be used with a clear understanding of the impact on task execution behavior.

## Requirements
- **Python:** Python 3.11 or higher.
- **Pynenc:** The `pynenc` library must be installed.

## Project Structure
- `tasks.py`: Defines tasks with different concurrency control settings.
- `sample.py`: Contains the script to demonstrate various concurrency control mechanisms in action.

## Running the Example
1. **Setup the Python Environment:**
   - Ensure Python 3.11 is installed and create a virtual environment.
   - Install `pynenc` by running `pip install pynenc`.

2. **Understanding the Tasks:**
   - `get_own_invocation_id`: A task without concurrency control.
   - `get_own_invocation_id_registration_concurrency`: A task with registration concurrency control.
   - `sleep_without_running_concurrency` and `sleep_with_running_concurrency`: Tasks designed to demonstrate running concurrency control.

3. **Execute the Sample Script:**
   - Run `sample.py` using the command: `python sample.py`.
   - The script will sequentially demonstrate different aspects of concurrency control:
     - Execution without concurrency control.
     - Task registration concurrency control.
     - Running tasks with and without running concurrency control.

## Understanding the Sample Script
- **Concurrency Control Mechanisms:**
  - The script showcases how concurrency control affects task execution, including scenarios where tasks are executed with intentional overlaps and sequential execution enforced by concurrency settings.
- **Task Execution Behavior:**
  - Detailed logging within `sample.py` provides insights into how tasks are executed, illustrating the effects of different concurrency control settings.

## Conclusion
The `concurrency_control` sample is intended to introduce some of the concurrency control capabilities available in `pynenc`. Through practical examples, it demonstrates basic configurations for managing task execution concurrency. This sample scratches the surface of what can be achieved with `pynenc`'s concurrency control features, focusing on a subset of available options without exploring more advanced aspects such as argument-based or key-based concurrency controls.
