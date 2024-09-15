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
    Set,
    Union,
    Protocol,
)

from hiku.executors.base import BaseExecutor
from hiku.result import Proxy


class SubmitRes(Protocol):
    def result(self) -> Any: ...


class Workflow:
    def result(self) -> Proxy:
        raise NotImplementedError(type(self))


class TaskSet:
    """A task set is a group of tasks (or futures) that are related and possibly
    dependent on each other.

    Task sets can spawn 'forked' task sets, which represent subgroups of tasks
    that can be processed separately but are associated with the parent task set
    """

    def __init__(self, queue: "Queue") -> None:
        self._queue = queue

    def submit(self, fn: Callable, *args: Any, **kwargs: Any) -> SubmitRes:
        return self._queue.submit(self, fn, *args, **kwargs)


# TODO: make queue generic over futures
class Queue:
    """
    A Queue is a class used to manage a collection of tasks (or 'futures')
    for execution.

    By default, tasks are grouped into task sets.

    Each task set can also 'fork' new task sets.
    Forking is a way to represent a dependency graph of execution.
    """

    def __init__(self, executor: BaseExecutor) -> None:
        self._executor = executor
        """
        A dictionary of futures sets associated with each task set.
        """
        self._futures: Dict[TaskSet, Set[SubmitRes]] = {}
        """
        A dictionary of forked task sets associated with each task set.
        """
        self._forks: Dict[TaskSet, Set[TaskSet]] = {}
        """
        A dictionary of callbacks associated with each future or task set.
        """
        self._callbacks: DefaultDict[Union[SubmitRes, TaskSet], List] = (
            defaultdict(list)
        )

    @property
    def __futures__(self) -> List[SubmitRes]:
        return list(chain.from_iterable(self._futures.values()))

    def progress(self, done: Iterable) -> None:
        """
        This method operates in two phases.

        The first phase is to iterate over completed tasks or 'futures' and
        remove them from their respective task set.
        For each completed future, it calls the corresponding callback functions

        A callback is usually a function that is either stores result of
        the future or spawns a new future into the queue.

        The second phase is to enter a loop, where it identifies completed task
        sets (a task set is considered completed if it doesn't have any futures
            or forks associated with it).
        For each completed task set, it calls the corresponding callback
        functions and removes the task set from the queue.

        If a task set has forks (task sets that were spawned from it),
        those forks are also removed from the respective fork set.

        This process continues until there are no pending task sets left.
        """
        for future_set in self._futures.values():
            future_set.difference_update(done)

        for fut in done:
            for callback in self._callbacks.pop(fut, []):
                callback()

        while True:
            completed_task_sets = [
                ts
                for ts in self._futures.keys()
                if not self._futures[ts] and not self._forks[ts]
            ]
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
        self, task_set: "TaskSet", fn: Callable, *args: Any, **kwargs: Any
    ) -> SubmitRes:
        fut = self._executor.submit(fn, *args, **kwargs)
        self._futures[task_set].add(fut)
        return fut

    def fork(self, from_: Optional["TaskSet"]) -> "TaskSet":
        """
        Forked task sets represent child task sets of a parent task set.

        The parent task set is considered done when all its futures
        and its forked task sets are done.
        """
        task_set = TaskSet(self)
        self._futures[task_set] = set()
        self._forks[task_set] = set()
        if from_ is not None:
            self._forks[from_].add(task_set)
        return task_set

    def add_callback(
        self, obj: Union[SubmitRes, "TaskSet"], callback: Callable
    ) -> None:
        self._callbacks[obj].append(callback)
