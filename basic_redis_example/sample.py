import logging
import time

import tasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_distributed_add() -> None:
    logger.info("Running distributed add")
    start_time = time.time()
    invocation = tasks.add(4, 4)
    logger.info(f"Distributed invocation: {invocation=}")
    if invocation.result != 8:
        raise ValueError(f"Expected 8, got {invocation.result}")
    end_time = time.time()
    logger.info(f"Distributed add time: {end_time - start_time} seconds")


def run_parallel_sleep(sleep_args: list[int]) -> None:
    logger.info("Running parallel sleep (PS)")
    start_time = time.time()
    invocations = [tasks.sleep(i) for i in sleep_args]
    results: list[int] = []
    # in this case invocations is a list of Invocation objects
    # the iterator will block waiting for results in the order of the list
    for invocation in invocations:
        logger.info(f"(PS)Waiting for {invocation.task.args=} to finish")
        # invocation.result will block until result is available
        logger.info(
            f"(PS)Done, {invocation.task.args=} sleept for {invocation.result} seconds"
        )
        results.append(invocation.result)
    if results != sleep_args:
        raise ValueError(f"(PS)Expected {sleep_args}, got {results}")
    end_time = time.time()
    logger.info(f"(PS)Parallel sleep time: {end_time - start_time} seconds")


def run_sleep_using_parallelize(sleep_args: list[int]) -> None:
    logger.info("Running sleep using parallelize (PSUP)")
    start_time = time.time()
    invocation_group = tasks.sleep.parallelize([(i,) for i in sleep_args])
    results: list[int] = []
    # results: list[int] = []
    # in this case invocation_group is a InvocationGroup object,
    # __iter__ will return an iterator that will block until any of the task is available
    # without following the order of the distributed invocation list
    for result in invocation_group.results:
        logger.info(f"(PSUP)Done, result on parallelize {result} seconds")
        results.append(result)
    logger.info(f"(PSUP)Parallel invocation: {invocation_group=}")
    if set(results) != set(sleep_args):
        raise ValueError(
            f"(PSUP)Expected set {sleep_args}, got {invocation_group.results}"
        )
    if sorted(results) != results:
        # sorted ascending by the sleep time
        raise ValueError(f"(PSUP)Expected that results are sorted, but got {results}")
    end_time = time.time()
    logger.info(f"(PSUP)Parallel sleep time: {end_time - start_time} seconds")


if __name__ == "__main__":
    run_distributed_add()
    calls = 5
    sleep_args: list[int] = list(range(calls, 0, -1))
    time.sleep(1)
    run_parallel_sleep(sleep_args)
    time.sleep(1)
    run_sleep_using_parallelize(sleep_args)
