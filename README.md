# Samples for Pynenc

## Overview
This repository contains sample implementations demonstrating the usage of the [pynenc](https://github.com/pynenc/pynenc) library. Each example is a **self-contained project** with its own virtual environment and dependencies.

## Quick Start

Each example is isolated. To run any example:

```bash
cd <example_folder>
uv sync
uv run python sample.py
```

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — install with:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

## Available Samples

| Sample | Description |
| ------ | ----------- |
| [auto_orchestration](./auto_orchestration/README.md) | Automatic orchestration with recursive Fibonacci — shows how pynenc manages task dependencies and execution order. |
| [basic_local_threaded_example](./basic_local_threaded_example/README.md) | Simple local-threaded environment demo — ideal for understanding basic functionalities in a non-distributed setup. |
| [basic_redis_example](./basic_redis_example/README.md) | Distributed task processing with Redis — includes Docker Compose setup with multiple workers. |
| [concurrency_control](./concurrency_control/README.md) | Concurrency control settings — disabling concurrent execution, task-level concurrency for registration and running states. |
| [recovery_demo](./recovery_demo/README.md) | Automatic crash recovery — demonstrates heartbeat monitoring and task recovery when a worker is killed mid-execution. |
| [mem_unit_testing](./mem_unit_testing/README.md) | Unit testing pattern using in-memory components with ThreadRunner. |
| [sync_unit_testing](./sync_unit_testing/README.md) | Unit testing pattern using synchronous dev mode for simple inline execution. |

## CI & Testing

Every sample is tested in CI via GitHub Actions. The system works as follows:

- **[samples.yml](./samples.yml)** is the manifest — every sample directory must be listed with its test command, required services, and whether it appears in the pynenc docs.
- **GitHub Actions** run each sample automatically, grouped by required services (simple vs Redis vs other backends).
- **[test_samples_coverage.py](./test_samples_coverage.py)** is a validation test ensuring:
  - Every directory is either listed in the manifest or explicitly excluded
  - Every documented sample (referenced in [docs.pynenc.org](https://docs.pynenc.org)) has CI enabled
  - No phantom entries exist in the manifest

### Adding a new sample

1. Create the sample directory with a `pyproject.toml`
2. Add it to `samples.yml` with `ci: true` and a `test_command`
3. If it needs external services (Redis, MongoDB, etc.), add them to `services`
4. Run `uv run pytest test_samples_coverage.py` to verify coverage

## Additional Resources
- **Main GitHub Repository:** [github.com/pynenc/pynenc](https://github.com/pynenc/pynenc)
- **Official Website:** [pynenc.org](https://pynenc.org)
- **Documentation:** [docs.pynenc.org](https://docs.pynenc.org)

## License
Refer to the LICENSE file in the main [pynenc repository](https://github.com/pynenc/pynenc) for licensing information.
