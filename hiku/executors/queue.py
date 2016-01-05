from weakref import WeakKeyDictionary
from itertools import chain
from collections import defaultdict


class Workflow(object):

    def result(self):
        raise NotImplementedError


class TaskSet(object):

    def __init__(self, queue):
        self._queue = queue

    def submit(self, fn, *args, **kwargs):
        return self._queue.submit(self, fn, *args, **kwargs)


class Queue(object):

    def __init__(self, executor):
        self._executor = executor
        self._futures = WeakKeyDictionary()
        self._callbacks = defaultdict(list)

    @property
    def __futures__(self):
        return list(chain.from_iterable(self._futures.values()))

    def progress(self, done):
        for futures in self._futures.values():
            futures.difference_update(done)

        for fut in done:
            callbacks = self._callbacks.pop(fut, [])
            for callback in callbacks:
                callback(fut.result())

        completed_sets = [
            task_set for task_set, futures in self._futures.items()
            if not futures
        ]
        for task_set in completed_sets:
            self._futures.pop(task_set)
            callbacks = self._callbacks.pop(task_set, [])
            for callback in callbacks:
                callback()

    def submit(self, task_set, fn, *args, **kwargs):
        fut = self._executor.submit(fn, *args, **kwargs)
        self._futures[task_set].add(fut)
        return fut

    def fork(self):
        task_set = TaskSet(self)
        self._futures[task_set] = set()
        return task_set

    def add_callback(self, obj, callback):
        self._callbacks[obj].append(callback)
