import abc
from typing import (
    Callable,
    Any,
    TYPE_CHECKING,
    Union,
)


if TYPE_CHECKING:
    from hiku.result import Proxy
    from hiku.executors.queue import (
        Queue,
        Workflow,
    )


class BaseExecutor(abc.ABC):
    @abc.abstractmethod
    def submit(self, fn: Callable, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError


class BaseSyncExecutor(BaseExecutor):
    @abc.abstractmethod
    def process(self, queue: "Queue", workflow: "Workflow") -> "Proxy":
        raise NotImplementedError


class BaseAsyncExecutor(BaseExecutor):
    @abc.abstractmethod
    async def process(self, queue: "Queue", workflow: "Workflow") -> "Proxy":
        raise NotImplementedError


SyncAsyncExecutor = Union[BaseSyncExecutor, BaseAsyncExecutor]
