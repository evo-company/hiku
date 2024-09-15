from concurrent.futures import (
    wait,
    FIRST_COMPLETED,
    Executor,
    Future,
)
from typing import (
    TYPE_CHECKING,
    Callable,
    Any,
)

from hiku.executors.base import BaseSyncExecutor
from hiku.result import Proxy

if TYPE_CHECKING:
    from hiku.executors.queue import (
        Queue,
        Workflow,
    )


class ThreadsExecutor(BaseSyncExecutor):
    def __init__(self, pool: Executor):
        self._pool = pool

    def submit(self, fn: Callable, *args: Any, **kwargs: Any) -> Future:
        return self._pool.submit(fn, *args, **kwargs)

    def process(self, queue: "Queue", workflow: "Workflow") -> Proxy:
        while queue.__futures__:
            done, _ = wait(
                queue.__futures__, return_when=FIRST_COMPLETED  # type: ignore
            )
            queue.progress(done)
        return workflow.result()
