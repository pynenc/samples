# Samples for Pynenc

## Overview
This repository contains various sample implementations that demonstrate the usage of the `pynenc` library. These examples are designed to help users understand the capabilities of `pynenc` and how it can be integrated into different applications.

Each sample in this repository showcases different features or use cases of `pynenc`. Below is a list of the available samples with links to their detailed documentation.

## Available Samples

| Sample Name          | Description |
| -------------------- | ----------- |
| [basic_local_threaded_example](./basic_local_threaded_example/README.md) | Provides a simple demonstration of using `pynenc` in a local-threaded environment, ideal for understanding basic functionalities in a non-distributed setup. |
| [basic_redis_example](./basic_redis_example/README.md) | Demonstrates the basic setup and usage of `pynenc` with Redis for distributed task processing. It includes instructions for running with Docker, a local Redis server, and in development mode. |
| [concurrency_control](./concurrency_control/README.md) | Demonstrates various settings for concurrency control, such as disabling concurrent execution or enforcing task-level concurrency for registration and running states. |
| [auto_orchestration](./auto_orchestration/README.md) | Showcases automatic orchestration capabilities of `pynenc`, using a recursive Fibonacci function to illustrate how the library manages task dependencies and execution order. |


## Setting Up a Common Python Environment
To run these examples, you'll need Python 3.11 and a virtual environment. Here's how to set it up:

### Navigate to the `samples` Folder
```bash
cd path/to/samples
```

### Create the Virtual Environment
Create a virtual environment named `venv`:
```bash
python3.11 -m venv venv
```
This command creates a new folder named `venv` in your `samples` directory, containing the Python environment.

### Activate the Virtual Environment
Activate the virtual environment:
- **Windows:**
  ```cmd
  venv\Scripts\activate
  ```
- **Unix/MacOS:**
  ```bash
  source venv/bin/activate
  ```
Your command prompt should now indicate that the virtual environment is active, shown as `(venv)`.

### Install `pynenc`
Install `pynenc` within the virtual environment:
```bash
pip install pynenc
```

### Verify the Installation
Check the installed packages:
```bash
pip list
```
Ensure that `pynenc` appears in the list.

Remember to activate this environment whenever you work with these samples.

## Additional Resources
- **Main GitHub Repository:** For more information about the `pynenc` library, visit the [GitHub repository](https://github.com/pynenc/pynenc).
- **Official Website:** Learn more about `pynenc` at the [official website](https://pynenc.org).
- **Documentation:** Detailed documentation is available at [docs.pynenc.org](https://docs.pynenc.org).

## License
Refer to the LICENSE file in the main [pynenc repository](https://github.com/pynenc/pynenc) for licensing information.
