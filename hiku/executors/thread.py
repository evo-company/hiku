from concurrent.futures import wait, FIRST_COMPLETED


class ThreadExecutor(object):

    def __init__(self, pool):
        self.pool = pool

    def submit(self, fn, *args, **kwargs):
        return self.pool.submit(fn, *args, **kwargs)

    def process(self, query):
        query.begin()
        while query.futures:
            done, _ = wait(query.futures, return_when=FIRST_COMPLETED)
            query.progress(done)
        return query.result()
