from itertools import chain
from collections import defaultdict
from typing import (
    Callable,
    Any,
    Dict,
    DefaultDict,
    List,
    Optional,
    Iterable,
    Union,
)

from typing_extensions import Protocol

from hiku.executors.base import BaseExecutor
from hiku.result import Proxy


class SubmitRes(Protocol):
    def result(self) -> Any: ...


class Workflow:

    def result(self) -> Proxy:
        raise NotImplementedError(type(self))


class TaskSet:

    def __init__(self, queue: 'Queue') -> None:
        self._queue = queue

    def submit(
        self, fn: Callable, *args: Any, **kwargs: Any
    ) -> SubmitRes:
        return self._queue.submit(self, fn, *args, **kwargs)


# TODO: make queue generic over futures
class Queue:

    def __init__(self, executor: BaseExecutor) -> None:
        self._executor = executor
        self._futures: Dict = {}
        self._forks: Dict = {}
        self._callbacks: DefaultDict[Union[SubmitRes, TaskSet], List] = defaultdict(list)  # noqa: E501

    @property
    def __futures__(self) -> List:
        return list(chain.from_iterable(self._futures.values()))

    def progress(self, done: Iterable) -> None:
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

    def submit(
        self,
        task_set: 'TaskSet',
        fn: Callable,
        *args: Any,
        **kwargs: Any
    ) -> SubmitRes:
        fut = self._executor.submit(fn, *args, **kwargs)
        self._futures[task_set].add(fut)
        return fut

    def fork(self, from_: Optional['TaskSet']) -> 'TaskSet':
        task_set = TaskSet(self)
        self._futures[task_set] = set()
        self._forks[task_set] = set()
        if from_ is not None:
            self._forks[from_].add(task_set)
        return task_set

    def add_callback(
        self, obj: Union[SubmitRes, 'TaskSet'], callback: Callable
    ) -> None:
        self._callbacks[obj].append(callback)
