from typing import (
    Generic,
    TypeVar,
    Callable,
    TYPE_CHECKING,
    Any,
)

from hiku.executors.base import BaseSyncExecutor
from hiku.result import Proxy

if TYPE_CHECKING:
    from hiku.executors.queue import (
        Queue,
        Workflow,
    )


T = TypeVar("T")


class FutureLike(Generic[T]):
    def __init__(self, result: T) -> None:
        self._result = result

    def result(self) -> T:
        return self._result


class SyncExecutor(BaseSyncExecutor):
    def submit(self, fn: Callable, *args: Any, **kwargs: Any) -> FutureLike:
        return FutureLike(fn(*args, **kwargs))

    def process(self, queue: "Queue", workflow: "Workflow") -> Proxy:
        while queue.__futures__:
            queue.progress(queue.__futures__)
        return workflow.result()
