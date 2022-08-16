from hiku.executors.base import BaseSyncExecutor as BaseSyncExecutor
from hiku.executors.queue import Queue as Queue, Workflow as Workflow
from hiku.result import Proxy as Proxy
from typing import Any, Callable, TypeVar

T = TypeVar('T')

class FutureLike:
    def __init__(self, result: T) -> None: ...
    def result(self) -> T: ...

class SyncExecutor(BaseSyncExecutor):
    def submit(self, fn: Callable, *args: Any, **kwargs: Any) -> FutureLike: ...
    def process(self, queue: Queue, workflow: Workflow) -> Proxy: ...
