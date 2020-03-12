from abc import ABC, abstractmethod


class LifeCycle(ABC):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def is_running(self) -> bool:
        pass

    @abstractmethod
    def is_started(self) -> bool:
        pass

    @abstractmethod
    def is_starting(self) -> bool:
        pass

    @abstractmethod
    def is_stopping(self) -> bool:
        pass

    @abstractmethod
    def is_stopped(self) -> bool:
        pass

    @abstractmethod
    def is_failed(self) -> bool:
        pass
