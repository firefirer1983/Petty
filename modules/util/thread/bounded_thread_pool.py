import time

from ..component.abstract_lifecycle import AbstractLifeCycle
from .thread_pool import ThreadPool
from threading import Lock, Thread, Condition
from ...runnable import Runnable
from queue import Queue, Empty, Full
from threading import RLock


class CanceledException(Exception):
    def __str__(self):
        return "Thread Canceled!"

    pass


class ThreadPoolOverloadException(Exception):
    def __str__(self):
        return "Thread Canceled!"


class ThreadPoolNotReadyException(Exception):
    def __str__(self):
        return "Thread Pool Not Ready"


class BoundedThreadPool(AbstractLifeCycle, ThreadPool):

    _pool_id = 0
    MAX_THREADS = 255
    MIN_THREADS = 1
    TASK_QUEUE_SIZE = 255

    def __init__(self):
        super().__init__()
        self._thread_id = 0
        self._task_queue = Queue(self.TASK_QUEUE_SIZE)
        self._idle_threads = Queue(self.MAX_THREADS)
        self._daemon = False
        self._thread_cnt = 0
        self._pool_lock = RLock()
        self._last_shrink = time.time()
        self._low_threads = 0
        self._name = "btpool" + str(self._pool_id)
        self._max_idle_time_ms = 60000

    def get_task(self, timeout=1):
        try:
            task_ = self._task_queue.get(timeout=timeout)
        except Empty as e:
            return None
        else:
            self._task_queue.task_done()
            return task_

    def join_idle(self, th):
        return self._idle_threads.put(th)

    def _enqueue_task(self, job: Runnable):
        try:
            self._task_queue.put(job)
            return True
        except Full as e:
            return False

    def dispatch(self, job: Runnable):

        if not self.is_running():
            raise ThreadPoolNotReadyException()

        while True:
            spawn_ = False
            if self._idle_threads.empty():
                spawn_ = True

            try:
                self._task_queue.put(job)
            except Full as e:
                spawn_ = True

            if spawn_ and self.is_overload:
                raise ThreadPoolOverloadException()

            if spawn_:
                with self._pool_lock:
                    th_ = PoolThread(self, self._daemon)
                    th_.start()
                    self._thread_cnt += 1

            try:
                _idle = self._idle_threads.get(timeout=1)
                self._idle_threads.task_done()
                _idle.wakeup()
            except Empty as e:
                print("warn: no idle thread!: %s" % str(e))
            else:
                break

    def join(self):
        self.stop()

    def do_start(self):
        pass

    def do_stop(self):
        while True:
            try:
                th = self._idle_threads.get(timeout=1)
                self._idle_threads.task_done()
                th.wakeup()
            except Empty as e:
                print(str(e))
                break
        self._idle_threads.join()

    @property
    def max_idle_time_ms(self) -> int:
        return self._max_idle_time_ms

    @property
    def last_shrink(self):
        return self._last_shrink

    def set_last_shrink(self, val: float):
        self._last_shrink = val

    def decrease_thread_cnt(self):
        with self._pool_lock:
            self._thread_cnt -= 1

    @property
    def is_overload(self):
        return self._thread_cnt >= self.MAX_THREADS

    @property
    def is_idle_sufficient(self):
        return self._idle_threads.full()

    def get_threads(self):
        return self._thread_cnt

    def get_idle_threads(self):
        return self._idle_threads.qsize()

    def is_low_on_threads(self):
        return self._idle_threads.qsize() < self._low_threads

    def set_low_threads(self, num: int):
        self._low_threads = num

    @property
    def daemon(self):
        return self._daemon

    def set_daemon(self, value: bool):
        self._daemon = value

    def __repr__(self):
        return str(self._name)

    def __str__(self):
        return repr(self)


class PoolThread(Thread):
    def __init__(self, pool: BoundedThreadPool, daemon=False):
        super().__init__()
        self._pool = pool
        self.setDaemon(daemon)
        self._cond = Condition()
        self._busy = False

    def run(self):
        while True:
            task_ = self._pool.get_task()
            if task_:
                try:
                    task_.run()
                except Exception as e:
                    raise e

                continue

            if not self._pool.is_running():
                break

            now_ = time.time()
            if self._overtime(now_):
                self._pool.set_last_shrink(now_)
                break
            else:
                with self._cond:
                    self._pool.join_idle(self)
                    self._cond.wait()

        self._pool.decrease_thread_cnt()

    def _overtime(self, now):
        if now - self._pool.last_shrink > self._pool.max_idle_time_ms / 1000.0:
            return True
        else:
            return False

    def wakeup(self) -> bool:
        with self._cond:
            self._cond.notify()
        return True

    def is_busy(self):
        return self._busy
