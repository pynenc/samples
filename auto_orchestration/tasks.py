from pynenc import Pynenc

app = Pynenc()


@app.task
def fibonacci(n: int) -> int:
    # Do not stress, soon a sample with distributed memoization will be available
    fibonacci.logger.info(f"Calculating fibonacci({n})")
    if n <= 1:
        result = n
    else:
        result = fibonacci(n - 1).result + fibonacci(n - 2).result
    fibonacci.logger.info(f"Result of fibonacci({n}) is {result}")
    return result
