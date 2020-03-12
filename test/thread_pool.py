from modules.util.thread.bounded_thread_pool import BoundedThreadPool
from modules.runnable import Runnable


class Hello(Runnable):
    def run(self):
        print("Hello")


def main():
    pool = BoundedThreadPool()
    pool.start()
    for i in range(15):
        pool.dispatch(Hello())
    print("done hello")
    pool.join()


if __name__ == "__main__":
    main()
