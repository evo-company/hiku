from asyncio import wait, FIRST_COMPLETED

from .base import process_wait_list


class AsyncIOExecutor(object):

    def __init__(self, loop):
        self._loop = loop
        self._futures = set()
        self._wait_list = []

    def submit(self, fn, *args, **kwargs):
        fut = self._loop.create_task(fn(*args, **kwargs))
        self._futures.add(fut)
        return fut

    def wait(self, futures, callback):
        self._wait_list.append((set(futures), callback))

    def process(self, query):
        query.begin()
        while self._futures:
            done, _ = yield from wait(self._futures,
                                      return_when=FIRST_COMPLETED)
            self._wait_list = list(process_wait_list(self._wait_list, done))
            self._futures.difference_update(done)
        return query.result()
