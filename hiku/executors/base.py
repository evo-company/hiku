import abc
from typing import (
    Callable,
    Any,
)


class BaseExecutor(abc.ABC):
    @abc.abstractmethod
    def submit(self, fn: Callable, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

