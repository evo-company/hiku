from asyncio import wait, FIRST_COMPLETED


class AsyncIOExecutor(object):

    def __init__(self, loop):
        self._loop = loop
        self._futures = set()

    def submit(self, fn, *args, **kwargs):
        fut = self._loop.create_task(fn(*args, **kwargs))
        self._futures.add(fut)
        return fut

    def process(self, query):
        query.begin()
        while self._futures:
            done, _ = yield from wait(self._futures,
                                      return_when=FIRST_COMPLETED)
            query.progress(done)
            self._futures.difference_update(done)
        return query.result()
