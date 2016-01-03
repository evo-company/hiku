from concurrent.futures import wait, FIRST_COMPLETED

from .base import process_wait_list


class ThreadExecutor(object):

    def __init__(self, pool):
        self._pool = pool
        self._futures = set()
        self._wait_list = []

    def submit(self, fn, *args, **kwargs):
        fut = self._pool.submit(fn, *args, **kwargs)
        self._futures.add(fut)
        return fut

    def wait(self, futures, callback):
        self._wait_list.append((set(futures), callback))

    def process(self, query):
        query.begin()
        while self._futures:
            done, _ = wait(self._futures, return_when=FIRST_COMPLETED)
            self._wait_list = list(process_wait_list(self._wait_list, done))
            self._futures.difference_update(done)
        return query.result()
