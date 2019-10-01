import inspect

from asyncio import wait, FIRST_COMPLETED, gather, CancelledError
from asyncio import get_event_loop


class AsyncIOExecutor:

    def __init__(self, loop=None):
        self._loop = loop or get_event_loop()

    def submit(self, fn, *args, **kwargs):
        coro = fn(*args, **kwargs)
        if not inspect.isawaitable(coro):
            raise TypeError('{!r} returned non-awaitable object {!r}'
                            .format(fn, coro))
        return self._loop.create_task(coro)

    async def process(self, queue, workflow):
        try:
            while queue.__futures__:
                done, _ = await wait(queue.__futures__,
                                     return_when=FIRST_COMPLETED)
                queue.progress(done)
            return workflow.result()
        except CancelledError:
            for task in queue.__futures__:
                task.cancel()
            await gather(*queue.__futures__)
            raise
