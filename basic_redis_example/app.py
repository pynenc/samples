from pynenc import PynencBuilder

app = PynencBuilder().app_id("app_basic_redis_example").redis(url="redis://redis").multi_thread_runner().build()
