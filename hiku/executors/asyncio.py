from asyncio import wait, FIRST_COMPLETED


class AsyncIOExecutor(object):

    def __init__(self, loop):
        self._loop = loop

    def submit(self, fn, *args, **kwargs):
        return self._loop.create_task(fn(*args, **kwargs))

    async def process(self, queue, workflow):
        while queue.__futures__:
            done, _ = await wait(queue.__futures__,
                                 loop=self._loop,
                                 return_when=FIRST_COMPLETED)
            queue.progress(done)
        return workflow.result()
