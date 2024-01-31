import time

from pynenc import Pynenc

app = Pynenc()


@app.task
def add(x: int, y: int) -> int:
    # add logger will add task and invocation ids to the log
    add.logger.info(f"{add.task_id=} Adding {x} + {y}")
    return x + y
