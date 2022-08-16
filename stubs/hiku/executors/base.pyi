import abc
from hiku.executors.queue import Queue as Queue, Workflow as Workflow
from hiku.result import Proxy as Proxy
from typing import Any, Callable, Union

class BaseExecutor(abc.ABC, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def submit(self, fn: Callable, *args: Any, **kwargs: Any) -> Any: ...

class BaseSyncExecutor(BaseExecutor, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def process(self, queue: Queue, workflow: Workflow) -> Proxy: ...

class BaseAsyncExecutor(BaseExecutor, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def process(self, queue: Queue, workflow: Workflow) -> Proxy: ...
SyncAsyncExecutor = Union[BaseSyncExecutor, BaseAsyncExecutor]
