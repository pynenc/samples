# basic_redis_example

## Introduction
`basic_redis_example is a sample project demonstrating the basic setup and usage of the `pynenc` library with Redis for distributed task processing. This example can be run in a containerized environment using Docker Compose or directly on your local machine if you have Redis and Python installed.

## Requirements
- **Docker (Optional):** If you prefer a containerized setup, ensure Docker and Docker Compose are installed on your system.
- **Python:** Python 3.11 is required. The Docker container will handle the Python environment if using Docker.
- **Redis:** A Redis server is needed. You can use a local installation or the Docker container.

## Project Structure
- `Dockerfile`: Sets up the Python environment, installs `pynenc`, and copies the sample Python code into the container (used in Docker setup).
- `docker-compose.yml`: Configures the services - a Redis server and the Python environment running `pynenc` (used in Docker setup).
- `app.py`: Initializes the Pynenc application.
- `sample.py`: A Python script for demonstrating task execution using `pynenc`.
- `tasks.py`: Contains the task definitions used in the sample.
- `pyproject.toml`: Configuration settings for `pynenc` to run with Redis using the `ProcessRunner`.
- `__init__.py`: An empty file to treat the directory as a Python module.

## Configuration
The project uses a `pyproject.toml` file for configuration. The settings in this file are tailored to run all components with Redis and utilize the `ProcessRunner` for running tasks in separate processes.

`pyproject.toml` contents:
```toml
[tool.pynenc]
app_id = "app_basic_redis_example"
orchestrator_cls = "RedisOrchestrator"
broker_cls = "RedisBroker"
state_backend_cls = "RedisStateBackend"
serializer_cls = "JsonSerializer"
runner_cls = "ProcessRunner"

[tool.pynenc.redis]
redis_host = "redis"
```

## Setup and Execution
### Using Docker (Primary Method)
1. **Building the Containers:**
   - Run `docker-compose build` to build the Python container and pull the Redis image.

2. **Running the Services:**
   - Execute `docker-compose up` to start the Redis server and the `pynenc` environment.
   - The `pynenc` runners will start automatically, executing `pynenc --app=app.app runner start`.
   - To run the services in the background, use `docker-compose up -d`.

3. **Monitoring the Services:**
   - Use `docker-compose ps` to check the status of the services.
   - To view the logs, use `docker-compose logs`. For real-time logs, add the `-f` flag: `docker-compose logs -f`.

4. **Stopping the Services:**
   - When finished, use `docker-compose down` to stop and remove the containers, networks, and volumes.

5. **Triggering Tasks:**
   - The Python environment includes `sample.py` to trigger tasks and wait for the results. This script is executed automatically after the Redis service is up.

### Without Docker (Alternative Method)
1. **Install Redis:**
   - Install Redis on your local machine. Instructions can be found at [Redis Installation](https://redis.io/docs/install/install-redis/).

2. **Install Pynenc:**
   - Ensure Python 3.11 is installed and then run `pip install pynenc`.

3. **Configure Redis Host:**
   - Set the Redis host environment variable to point to your local Redis instance: `export PYNENC__CONFIGREDIS__REDIS_HOST=localhost`.
   - Alternatively, you can specify the Redis host configuration in the `pyproject.toml` file.

4. **Running the Worker:**
   - Start a `pynenc` worker with `pynenc --app=app.app runner start`.

5. **Triggering Tasks:**
   - Run `sample.py` to trigger the tasks: `python sample.py`.
   - Note: If you haven't set the Redis host in step 3 or in `pyproject.toml`, you can specify it inline when running the script:
     ```bash
     PYNENC__CONFIGREDIS__REDIS_HOST=localhost python sample.py
     ```

### Running in Development Mode (Alternative Method)

You can run the `BasicRedisExample` in development mode, which simplifies the execution environment and does not require Redis or any runners. This mode is particularly useful for debugging or testing the basic functionality of your tasks.

To run in development mode, execute the sample script with the `PYNENC__DEV_MODE_FORCE_SYNC_TASKS` environment variable set to `True`:
```bash
PYNENC__DEV_MODE_FORCE_SYNC_TASKS=True python sample.py
```

#### How It Works
- In this mode, `pynenc` bypasses its distributed task processing mechanism. Instead, it executes any defined task directly and sequentially.
- This means that the tasks are called as regular Python functions without any asynchronous or parallel execution.

#### Limitations and Disclaimer
- **Sequential Execution:** Since tasks run sequentially in this mode, features that rely on parallel or asynchronous execution will not work as intended.
- **Sample Script Behavior:** The `sample.py` script will fail in development mode. This is because the script checks that tasks are executed in a different order than they were triggered, which relies on parallel execution. In development mode, tasks are executed sequentially, so the results of the fastest task will not be available first, as expected in the normal distributed mode. This behavior demonstrates a use case where development mode can affect the outcome of a function.


#### Use Case
- Development mode is ideal for initial testing and debugging, or when you want to run your tasks without setting up a complete distributed environment. It helps you verify the basic logic of your tasks before deploying them in a distributed setting.



### Configuration Options
- **Redis Host Configuration:**
  - For a quick and flexible setup, you can specify the Redis host using environment variables. This is particularly useful for changing configurations across different environments. For example, set the Redis host by using: `PYNENC__CONFIGREDIS__REDIS_HOST=localhost`.
  - As an alternative, the Redis host can be configured in the `pyproject.toml` file. This approach is better suited for more permanent configurations that do not change across environments. You can also use other configuration methods as detailed in [Pynenc Configuration](https://docs.pynenc.org/en/latest/configuration/configuration.html).


## Code Details
- `sample.py` demonstrates various ways of defining and executing tasks, including distributed and parallel execution.
- `tasks.py` contains the task definitions, showcasing how to use `pynenc` decorators to make functions distributable tasks.

## Conclusion
This sample provides a comprehensive demonstration of integrating `pynenc` with Redis for distributed task processing. It offers flexibility in setup and can be run in a containerized environment using Docker or directly on a local machine with a Redis server.
