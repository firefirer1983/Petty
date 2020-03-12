from abc import ABC, abstractmethod
from ...runnable import Runnable


class ThreadPool(ABC):
    @abstractmethod
    def dispatch(self, job: Runnable):
        pass

    @abstractmethod
    def join(self):
        pass

    @abstractmethod
    def get_threads(self):
        pass

    @abstractmethod
    def get_idle_threads(self):
        pass

    @abstractmethod
    def is_low_on_threads(self):
        pass
