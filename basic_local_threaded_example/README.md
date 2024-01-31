# Basic Local Threaded Example

## Introduction
The `basic_local_threaded_example` is a minimalistic demonstration of the `pynenc` library for task processing using local threading. This example illustrates how to execute tasks in different modes: using a separate thread, running synchronously on the main thread, and handling task timeouts.

## Important Disclaimer
This example utilizes `ThreadRunner` and default memory-based components (`Mem` components) of the `pynenc` library. These components operate within the memory space of the current Python interpreter process. As such, they are not suitable for distributed task processing across multiple processes or machines. This approach is only valid for tests or demonstration purposes and cannot be used in a production environment where distributed, multi-process, or multi-machine task execution is required.

## Requirements
- **Python:** Python 3.11 or higher.
- **Pynenc:** Ensure the `pynenc` library is installed.

## Project Structure
- `tasks.py`: Defines a simple `add` task using the `pynenc` library.
- `sample.py`: Demonstrates various ways of executing the `add` task: on a separate thread, synchronously on the main thread, and with a timeout.

## Running the Example
1. **Clone the Repository:**
   - Clone or download the `basic_local_threaded_example` repository to your local machine.

2. **Install Dependencies:**
   - Run `pip install pynenc` to install the required `pynenc` library.

3. **Execute the Sample Script:**
   - Run the `sample.py` script using Python: `python sample.py`.
   - The script will demonstrate three different modes of executing the `add` task:
     - On a separate thread using `run_add_on_thread`.
     - Synchronously on the main thread using `run_sync`.
     - With a timeout to handle cases where no worker is available to run the task using `run_without_worker_add`.

## Understanding the Sample Script
- The `run_add_on_thread` function starts a separate thread for task execution, demonstrating parallel processing.
- The `run_without_worker_add` function attempts to run the task with a timeout, showcasing how to handle scenarios where a task could hang indefinitely.
- The `run_sync` function forces the task to run synchronously, illustrating the behavior when tasks are not processed in parallel.

## Conclusion
This simple example serves as a starting point for understanding how to use the `pynenc` library for task processing in a threaded environment. It's an excellent resource for learning the basics of task execution using `pynenc`.
