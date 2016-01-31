from concurrent.futures import wait, FIRST_COMPLETED


class ThreadsExecutor(object):

    def __init__(self, pool):
        self._pool = pool

    def submit(self, fn, *args, **kwargs):
        return self._pool.submit(fn, *args, **kwargs)

    def process(self, queue, workflow):
        while queue.__futures__:
            done, _ = wait(queue.__futures__, return_when=FIRST_COMPLETED)
            queue.progress(done)
        return workflow.result()
