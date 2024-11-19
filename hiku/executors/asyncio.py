import inspect
from asyncio import (
    FIRST_COMPLETED,
    CancelledError,
    Task,
    gather,
    get_running_loop,
    wait,
)
from typing import TYPE_CHECKING, Any, Callable, Coroutine, cast

from hiku.executors.base import BaseAsyncExecutor
from hiku.result import Proxy

if TYPE_CHECKING:
    from hiku.executors.queue import Queue, Workflow


class AsyncIOExecutor(BaseAsyncExecutor):
    """AsyncIOExecutor is an executor that uses asyncio event loop to run tasks.

    By default it allows to run both synchronous and asynchronous tasks.
    To deny synchronous tasks set deny_sync to True.

    :param deny_sync: deny synchronous tasks -
                      raise TypeError if a task is not awaitable
    """

    def __init__(self, deny_sync: bool = False) -> None:
        self.deny_sync = deny_sync

    async def _wrapper(self, fn: Callable, *args: Any, **kwargs: Any) -> Any:
        result = fn(*args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        else:
            return result

    def submit(self, fn: Callable, *args: Any, **kwargs: Any) -> Task:
        loop = get_running_loop()

        coro = fn(*args, **kwargs)
        if not inspect.isawaitable(coro):
            if self.deny_sync:
                raise TypeError(
                    "{!r} returned non-awaitable object {!r}".format(fn, coro)
                )

            return loop.create_task(self._wrapper(fn, *args, **kwargs))

        coro = cast(Coroutine, coro)
        return loop.create_task(coro)

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
