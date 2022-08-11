from typing import (
    TypeVar,
    Callable,
    TYPE_CHECKING,
)

from typing_extensions import ParamSpec

from hiku.executors.base import BaseExecutor
from hiku.result import Proxy

if TYPE_CHECKING:
    from hiku.executors.queue import (
        Queue,
        Workflow,
    )


T = TypeVar('T')
P = ParamSpec('P')


class FutureLike:

    def __init__(self, result: T) -> None:
        self._result = result

    def result(self) -> T:
        return self._result


class SyncExecutor(BaseExecutor):

    def submit(
        self,
        fn: Callable[P, T],
        *args: P.args,
        **kwargs: P.kwargs
    ) -> FutureLike:
        return FutureLike(fn(*args, **kwargs))

    def process(
        self,
        queue: 'Queue',
        workflow: 'Workflow'
    ) -> Proxy:
        while queue.__futures__:
            queue.progress(queue.__futures__)
        return workflow.result()
