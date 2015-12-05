from asyncio import wait, FIRST_COMPLETED


class AsyncIOExecutor(object):

    def __init__(self, loop):
        self.loop = loop

    def submit(self, fn, *args, **kwargs):
        return self.loop.create_task(fn(*args, **kwargs))

    def process(self, query):
        query.begin()
        while query.futures:
            done, _ = yield from wait(query.futures,
                                      return_when=FIRST_COMPLETED)
            query.progress(done)
        return query.result()
