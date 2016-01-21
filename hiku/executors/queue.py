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
        self._futures = {}
        self._forks = {}
        self._callbacks = defaultdict(list)

    @property
    def __futures__(self):
        return list(chain.from_iterable(self._futures.values()))

    def progress(self, done):
        for future_set in self._futures.values():
            future_set.difference_update(done)

        for fut in done:
            for callback in self._callbacks.pop(fut, []):
                callback()

        while True:
            completed_task_sets = [ts for ts in self._futures.keys()
                                   if not self._futures[ts] and
                                   not self._forks[ts]]
            if not completed_task_sets:
                break

            for task_set in completed_task_sets:
                for callback in self._callbacks.pop(task_set, []):
                    callback()
                self._futures.pop(task_set)
                self._forks.pop(task_set)
                for fork_set in self._forks.values():
                    fork_set.discard(task_set)

    def submit(self, task_set, fn, *args, **kwargs):
        fut = self._executor.submit(fn, *args, **kwargs)
        self._futures[task_set].add(fut)
        return fut

    def fork(self, from_):
        task_set = TaskSet(self)
        self._futures[task_set] = set()
        self._forks[task_set] = set()
        if from_ is not None:
            self._forks[from_].add(task_set)
        return task_set

    def add_callback(self, obj, callback):
        self._callbacks[obj].append(callback)
