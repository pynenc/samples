import time

from app import app


@app.task
def add(x: int, y: int) -> int:
    add.logger.info(f"{add.task_id=} Adding {x} + {y}")
    return x + y


@app.task
def sleep(x: int) -> int:
    add.logger.info(f"{sleep.task_id=} Sleeping for {x} seconds")
    time.sleep(x)
    add.logger.info(f"{sleep.task_id=} Done sleeping for {x} seconds")
    return x
