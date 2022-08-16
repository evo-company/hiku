from concurrent.futures import Executor, Future
from hiku.executors.base import BaseSyncExecutor as BaseSyncExecutor
from hiku.executors.queue import Queue as Queue, Workflow as Workflow
from hiku.result import Proxy as Proxy
from typing import Any, Callable

class ThreadsExecutor(BaseSyncExecutor):
    def __init__(self, pool: Executor) -> None: ...
    def submit(self, fn: Callable, *args: Any, **kwargs: Any) -> Future: ...
    def process(self, queue: Queue, workflow: Workflow) -> Proxy: ...
