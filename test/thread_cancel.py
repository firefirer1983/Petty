import ctypes
import inspect
import threading
import time


class StoppableThread(threading.Thread):
    def run(self):
        try:
            while True:
                time.sleep(1)
                print("alive ...")
        except Exception as e:
            print(str(e))

    def _get_my_tid(self):
        """determines this (self's) thread id

        CAREFUL : this function is executed in the context of the caller
        thread, to get the identity of the thread represented by this
        instance.
        """
        if not self.isAlive():
            raise threading.ThreadError("the thread is not active")

        # do we have it cached?
        if hasattr(self, "_thread_id"):
            return self._thread_id

        # no, look for it in the _active dict
        for tid, tobj in threading._active.items():
            if tobj is self:
                self._thread_id = tid
                return tid

        # TODO: in python 2.6, there's a simpler way to do : self.ident

        raise AssertionError("could not determine the thread's id")

    def raise_exception(self, exctype):
        thread_id = self._get_my_tid()
        """Raises an exception in the threads with id tid"""
        if not inspect.isclass(exctype):
            raise TypeError("Only types can be raised (not instances)")
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread_id), ctypes.py_object(exctype)
        )
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # "if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(thread_id), None
            )
            raise SystemError("PyThreadState_SetAsyncExc failed")


if __name__ == "__main__":
    th = StoppableThread()
    th.start()
    time.sleep(2)
    print("raise exception")
    th.raise_exception(SystemExit)
    th.join()
