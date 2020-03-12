from abc import ABC, abstractmethod
from .lifecycle import LifeCycle
from enum import IntEnum


class LifeCycleState(IntEnum):

    FAILED = -1
    STOPPED = 0
    STARTING = 1
    STARTED = 2
    STOPPING = 3


class AbstractLifeCycle(LifeCycle):
    def __init__(self):
        self._state = LifeCycleState.STOPPED

    def start(self):

        try:
            if self._state == LifeCycleState.STARTED:
                return
            self._state = LifeCycleState.STARTING
            self.do_start()
            self._state = LifeCycleState.STARTED
        except Exception as e:
            print(str(e))
            self._state = LifeCycleState.FAILED
            raise

    def stop(self):
        try:
            if (
                self._state == LifeCycleState.STOPPING
                or self._state == LifeCycleState.STOPPED
            ):
                return

            self._state = LifeCycleState.STOPPING
            self.do_stop()
            self._state = LifeCycleState.STOPPED
        except Exception as e:
            print(str(e))
            raise

    @abstractmethod
    def do_start(self):
        pass
    
    @abstractmethod
    def do_stop(self):
        pass

    def is_running(self) -> bool:
        return (
            self._state == LifeCycleState.STARTED
            or self._state == LifeCycleState.STARTING
        )

    def is_started(self) -> bool:
        return self._state == LifeCycleState.STARTED

    def is_starting(self) -> bool:
        return self._state == LifeCycleState.STARTING

    def is_stopping(self) -> bool:
        return self._state == LifeCycleState.STOPPING

    def is_stopped(self) -> bool:
        return self._state == LifeCycleState.STOPPED

    def is_failed(self) -> bool:
        return self._state == LifeCycleState.FAILED
