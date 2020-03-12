import ctypes
import time

from ..component.abstract_lifecycle import AbstractLifeCycle
from .thread_pool import ThreadPool
from threading import Lock, Thread, Condition
from ...runnable import Runnable
from queue import Queue


class CanceledException(Exception):
    def __str__(self):
        return "Thread Canceled!"

    pass


class BoundedThreadPool(AbstractLifeCycle, ThreadPool):

    _id = 0
    MAX_THREADS = 255
    MIN_THREADS = 1

    def __init__(self):
        self._id += 1
        self._lock = Lock()
        self._notify_lock = Lock()
        self._idle = list()
        self._warned = False
        self._daemon = False
        self._queue = list()
        self._threads = set()
        self._max_idle_time_ms = 60000
        self._last_shrink = time.time()
        self._name = "btpool" + str(self._id)
        self._low_threads = 0

    def dispatch(self, job: Runnable):
        with self._lock:
            if not self.is_running() or not job:
                return False

            idle = len(self._idle)
            if idle > 0:
                thread = self._idle.pop(0)
                thread.dispatch(job)
            else:
                if len(self._threads) < self.MAX_THREADS:
                    self._new_thread(job)
                else:
                    if not self._warned:
                        self._warned = True
                        print("Out of thread for %s" % self)
                    self._queue.append(job)

    def _new_thread(self, job: Runnable = None) -> Thread:
        with self._lock:
            self._id += 1
            th = PoolThread(self, job)
            self._threads.add(th)
            th.setName("%s - %u" % (self._name, self._id))
            th.start()
            return th

    def join(self):
        pass

    def do_start(self):
        for i in range(self.MIN_THREADS):
            self._new_thread(None)

    def do_stop(self):
        with self._lock:
            for th in self._threads:
                th.interrupt()

    def get_threads(self):
        return len(self._threads)

    def get_idle_threads(self) -> int:
        return len(self._idle)

    def is_low_on_threads(self):
        with self._lock:
            return len(self._idle) < self._low_threads

    def set_name(self, val: str):
        self._name = val

    def set_max_idle_time_ms(self, val: int):
        self._max_idle_time_ms = val

    def set_low_threads(self, num: int):
        self._low_threads = num

    @property
    def daemon(self):
        return self._daemon

    def set_daemon(self, value: bool):
        self._daemon = value

    @property
    def queue(self):
        return self._queue

    @property
    def warned(self) -> bool:
        return self._warned

    def set_warned(self, val: bool):
        self._warned = val

    def is_overload(self) -> bool:
        return len(self._threads) > self.MAX_THREADS

    def is_idle_sufficient(self):
        return len(self._idle) and len(self._threads) > self.MIN_THREADS

    @property
    def max_idle_time_ms(self) -> int:
        return self._max_idle_time_ms

    @property
    def last_shrink(self):
        return self._last_shrink

    def set_last_shrink(self, val: float):
        self._last_shrink = val

    def add_idle(self, idle: Thread):
        self._idle.append(idle)

    def remove_idle(self, idle: Thread):
        self._idle.remove(idle)

    def add_thread(self, th: Thread):
        self._threads.add(th)

    def remove_thread(self, th: Thread):
        self._threads.remove(th)

    @property
    def pool_lock(self):
        return self._lock

    def __str__(self):
        return self._name


class PoolThread(Thread):
    def __init__(self, pool: BoundedThreadPool, job: Runnable = None):
        self._job = job
        self._pool = pool
        self.setDaemon(self._pool.daemon)
        self._cond = Condition()
        self._canceled = False

    def run(self):
        try:
            with self._cond:
                job = self._job
                self._job = None

            while self._pool.is_running():
                if job:
                    todo = job
                    job = None
                    todo.run()
                else:
                    with self._pool.pool_lock:

                        if len(self._pool.queue) > 0:
                            # Got job in queue
                            job = self._pool.queue.pop(0)
                            continue

                        # Idle, no job to run for this thread, go check shrinking
                        if (
                            self._pool.is_overload()
                            or self._pool.is_idle_sufficient()
                        ):
                            now_ = time.time()
                            if (now_ - self._pool.last_shrink) > (
                                self._pool.max_idle_time_ms / 1000.0
                            ):
                                self._pool.set_last_shrink(now_)
                                return

                        # Idle , but not shrink, just add current thread in to idle
                        self._pool.add_idle(self)

                    try:
                        with self._cond:
                            if not self._job:
                                self._cond.wait()
                                if self._canceled:
                                    self._canceled = False
                                    raise CanceledException
                            job = self._job
                            self._job = None
                    except CanceledException as e:
                        print(str(e))
                    finally:
                        with self._pool.pool_lock:
                            self._pool.remove_idle(self)

        except Exception as e:
            print(str(e))
        finally:
            # 异常，将当前线程从线程池中溢出
            with self._pool.pool_lock:
                self._pool.remove_thread(self)

            with self._cond:
                job = self._job

            # 异常发生,但仍然存在job未完成
            if job and self._pool.is_running():
                self._pool.dispatch(job)

    def dispatch(self, job: Runnable):
        with self._cond:
            if self._job or not job:
                raise ValueError("Ivalid job")
            self._cond.notify()

    def interrupt(self):
        with self._cond:
            self._job = None
            self._canceled = True
            self._cond.notify()
