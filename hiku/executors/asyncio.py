from asyncio import wait, FIRST_COMPLETED, coroutine


class AsyncIOExecutor(object):

    def __init__(self, loop):
        self._loop = loop

    def submit(self, fn, *args, **kwargs):
        return self._loop.create_task(fn(*args, **kwargs))

    @coroutine
    def process(self, queue, workflow):
        while queue.__futures__:
            done, _ = yield from wait(queue.__futures__,
                                      loop=self._loop,
                                      return_when=FIRST_COMPLETED)
            queue.progress(done)
        return workflow.result()
