from modules.util.thread.bounded_thread_pool import BoundedThreadPool
from modules.runnable import Runnable


class Hello(Runnable):
    def run(self):
        print("Hello")


def test_pool_create():
    pool = BoundedThreadPool()
    pool.start()
    for i in range(15):
        pool.dispatch(Hello())
    pool.join()
