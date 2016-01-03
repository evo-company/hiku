from concurrent.futures import wait, FIRST_COMPLETED


class ThreadExecutor(object):

    def __init__(self, pool):
        self._pool = pool
        self._futures = set()

    def submit(self, fn, *args, **kwargs):
        fut = self._pool.submit(fn, *args, **kwargs)
        self._futures.add(fut)
        return fut

    def process(self, query):
        query.begin()
        while self._futures:
            done, _ = wait(self._futures, return_when=FIRST_COMPLETED)
            query.progress(done)
            self._futures.difference_update(done)
        return query.result()
