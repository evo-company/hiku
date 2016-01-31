class FutureLike(object):

    def __init__(self, result):
        self._result = result

    def result(self):
        return self._result


class SyncExecutor(object):

    def submit(self, fn, *args, **kwargs):
        return FutureLike(fn(*args, **kwargs))

    def process(self, queue, workflow):
        while queue.__futures__:
            queue.progress(queue.__futures__)
        return workflow.result()
