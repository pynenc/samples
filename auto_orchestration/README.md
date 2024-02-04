# Automatic Orchestration Example

## Introduction

The `auto_orchestration` sample showcases the automatic orchestration capabilities of the Pynenc library, particularly how it manages task dependencies. By utilizing a recursive Fibonacci function, this example demonstrates Pynenc's ability to handle tasks that depend on the results of other tasks, ensuring correct execution order and task completion.

## Important Disclaimer

This example emphasizes Pynenc's orchestration features within a single-threaded environment, leveraging the `ThreadRunner` for task execution. It's designed to illustrate the library's internal mechanisms for pausing and resuming tasks based on dependencies, not for high-performance computing or production-level distributed task processing.

## Requirements

- **Python:** Version 3.11 or higher.
- **Pynenc:** The latest version of the `pynenc` library.

## Project Structure

- `tasks.py`: Contains the Fibonacci task definition, highlighting recursive task calls within Pynenc.
- `sample.py`: Implements a function to execute the Fibonacci calculation in a separate thread, demonstrating Pynenc's automatic task orchestration.

## Running the Example

1. **Setup Environment:**
   Ensure Python 3.11 and Pynenc are installed in your environment.

2. **Execute the Sample:**
   Run `sample.py` with Python to initiate the Fibonacci task in a threaded environment:
   ```bash
   python sample.py
   ```
   Optionally, enable detailed logging to observe the orchestration process:
   ```bash
   PYNENC__LOGGING_LEVEL=DEBUG python sample.py
   ```

## Understanding the Sample Script

### Task Definition

The `fibonacci` task in `tasks.py` is defined to call itself recursively, mimicking the mathematical calculation of Fibonacci numbers. Pynenc's orchestration ensures that even with self-referential tasks, the execution order respects task dependencies.

### Automatic Orchestration

`run_fibonnaci_in_a_thread` in `sample.py` demonstrates how Pynenc automatically orchestrates task execution. When executing the Fibonacci calculation, Pynenc intelligently manages task dependencies, pausing tasks awaiting the results of dependent tasks and resuming them once the results are available.

## Conclusion

This example serves as a primer on Pynenc's automatic orchestration capabilities, using a familiar recursive problem to illustrate how the library handles task dependencies. While simple, it provides insight into the powerful features Pynenc offers for managing complex task dependencies in a structured and efficient manner.
