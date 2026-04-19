import time

from pynenc import Pynenc

app = Pynenc()


@app.task
def slow_task(task_num: int) -> str:
    """Simulates a long-running process (e.g., processing an order, generating a report).

    Takes 8 seconds to complete. If the worker crashes mid-execution, pynenc
    automatically recovers the task and re-runs it on a healthy worker.
    """
    slow_task.logger.info(f"[slow_task({task_num})] Starting — will run for 8 seconds")
    for second in range(8):
        time.sleep(1)
        slow_task.logger.info(f"[slow_task({task_num})] progress {second + 1}/8")
    result = f"task_{task_num}_completed"
    slow_task.logger.info(f"[slow_task({task_num})] Finished -> {result}")
    return result
