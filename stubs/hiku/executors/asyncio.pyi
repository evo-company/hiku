from asyncio import AbstractEventLoop, Task
from hiku.executors.base import BaseAsyncExecutor as BaseAsyncExecutor
from hiku.executors.queue import Queue as Queue, Workflow as Workflow
from hiku.result import Proxy as Proxy
from typing import Any, Callable, Optional

class AsyncIOExecutor(BaseAsyncExecutor):
    def __init__(self, loop: Optional[AbstractEventLoop] = ...) -> None: ...
    def submit(self, fn: Callable, *args: Any, **kwargs: Any) -> Task: ...
    async def process(self, queue: Queue, workflow: Workflow) -> Proxy: ...
