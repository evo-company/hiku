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
    """AsyncIOExecutor is an executor that uses asyncio event loop to run tasks.

    By default it allows to run both synchronous and asynchronous tasks.
    To deny synchronous tasks set deny_sync to True.

    :param loop: asyncio event loop
    :param deny_sync: deny synchronous tasks -
                      raise TypeError if a task is not awaitable
    """

    def __init__(
        self, loop: Optional[AbstractEventLoop] = None, deny_sync: bool = False
    ) -> None:
        self.loop = loop or get_event_loop()
        self.deny_sync = deny_sync

    async def _wrapper(self, fn: Callable, *args: Any, **kwargs: Any) -> Any:
        result = fn(*args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        else:
            return result

    def submit(self, fn: Callable, *args: Any, **kwargs: Any) -> Task:
        coro = fn(*args, **kwargs)
        if not inspect.isawaitable(coro):
            if self.deny_sync:
                raise TypeError(
                    "{!r} returned non-awaitable object {!r}".format(fn, coro)
                )

            return self.loop.create_task(self._wrapper(fn, *args, **kwargs))

        coro = cast(Coroutine, coro)
        return self.loop.create_task(coro)

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
