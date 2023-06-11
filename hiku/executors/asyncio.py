import inspect

from asyncio import (
    wait,
    FIRST_COMPLETED,
    gather,
    CancelledError,
    Task,
    AbstractEventLoop,
)
from asyncio import get_event_loop
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Coroutine,
    Optional,
    cast,
)

from hiku.executors.base import BaseAsyncExecutor
from hiku.result import Proxy


if TYPE_CHECKING:
    from hiku.executors.queue import (
        Queue,
        Workflow,
    )


class AsyncIOExecutor(BaseAsyncExecutor):
    def __init__(self, loop: Optional[AbstractEventLoop] = None) -> None:
        self._loop = loop or get_event_loop()

    def submit(self, fn: Callable, *args: Any, **kwargs: Any) -> Task:
        coro = fn(*args, **kwargs)
        if not inspect.isawaitable(coro):
            raise TypeError(
                "{!r} returned non-awaitable object {!r}".format(fn, coro)
            )
        coro = cast(Coroutine, coro)
        return self._loop.create_task(coro)

    async def process(self, queue: "Queue", workflow: "Workflow") -> Proxy:
        try:
            while queue.__futures__:
                done, _ = await wait(  # type: ignore
                    queue.__futures__, return_when=FIRST_COMPLETED
                )
                queue.progress(done)
            return workflow.result()
        except CancelledError:
            for task in queue.__futures__:
                task.cancel()  # type: ignore
            await gather(*queue.__futures__)  # type: ignore
            raise
