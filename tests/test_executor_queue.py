from functools import partial

import pytest

from hiku.executors.queue import Queue


class DummyFuture:
    def __init__(self, fn, args, kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.fn(*self.args, **self.kwargs)


class DummyExecutor:
    def submit(self, fn, *args, **kwargs):
        return DummyFuture(fn, args, kwargs)


def log_call(fn):
    def wrapper(results, *args, **kwargs):
        results.append("-> {}".format(fn.__name__))
        res = fn(results, *args, **kwargs)
        results.append("<- {}".format(fn.__name__))
        return res

    return wrapper


SCRIPT = [
    "-> level1_init",
    "<- level1_init",
    ".. level1_task1",
    "-> level1_task1_callback",
    "-> level2_init",
    "<- level2_init",
    "<- level1_task1_callback",
    ".. level2_task1",
    "-> level2_task1_callback",
    "-> level3_init",
    "<- level3_init",
    "<- level2_task1_callback",
    ".. level3_task1",
    "-> level3_task1_callback",
    "<- level3_task1_callback",
    ".. level3_task2",
    "-> level3_task2_callback",
    "<- level3_task2_callback",
    "-> level2_task_set3_callback",
    "<- level2_task_set3_callback",
    ".. level2_task2",
    "-> level2_task2_callback",
    "<- level2_task2_callback",
    "-> level1_task_set2_callback",
    "<- level1_task_set2_callback",
    ".. level1_task2",
    "-> level1_task2_callback",
    "<- level1_task2_callback",
    "-> level0_task_set1_callback",
    "<- level0_task_set1_callback",
]


def func(results, arg):
    results.append(".. {}".format(arg))


@log_call
def level1_init(results, queue):
    task_set1 = queue.fork(None)
    level1_task1 = task_set1.submit(func, results, "level1_task1")
    queue.add_callback(
        level1_task1, partial(level1_task1_callback, results, queue, task_set1)
    )
    queue.add_callback(task_set1, partial(level0_task_set1_callback, results))


@log_call
def level1_task1_callback(results, queue, task_set1):
    level2_init(results, queue, task_set1)


@log_call
def level2_init(results, queue, task_set1):
    task_set2 = queue.fork(task_set1)
    level2_task1 = task_set2.submit(func, results, "level2_task1")
    queue.add_callback(
        level2_task1, partial(level2_task1_callback, results, queue, task_set2)
    )
    queue.add_callback(
        task_set2, partial(level1_task_set2_callback, results, queue, task_set1)
    )


@log_call
def level2_task1_callback(results, queue, task_set2):
    level3_init(results, queue, task_set2)


@log_call
def level3_init(results, queue, task_set2):
    task_set3 = queue.fork(task_set2)
    level3_task1 = task_set3.submit(func, results, "level3_task1")
    queue.add_callback(
        level3_task1, partial(level3_task1_callback, results, queue, task_set3)
    )
    queue.add_callback(
        task_set3, partial(level2_task_set3_callback, results, queue, task_set2)
    )


@log_call
def level3_task1_callback(results, queue, task_set3):
    level3_task2 = task_set3.submit(func, results, "level3_task2")
    queue.add_callback(level3_task2, partial(level3_task2_callback, results))


@log_call
def level3_task2_callback(results):
    pass


@log_call
def level2_task_set3_callback(results, queue, task_set2):
    level2_task2 = task_set2.submit(func, results, "level2_task2")
    queue.add_callback(level2_task2, partial(level2_task2_callback, results))


@log_call
def level2_task2_callback(results):
    pass


@log_call
def level1_task_set2_callback(results, queue, task_set1):
    level1_task2 = task_set1.submit(func, results, "level1_task2")
    queue.add_callback(level1_task2, partial(level1_task2_callback, results))


@log_call
def level1_task2_callback(results):
    pass


@log_call
def level0_task_set1_callback(results):
    pass


@pytest.fixture(name="queue")
def _queue():
    return Queue(DummyExecutor())


@pytest.mark.parametrize("idx", [0, -1])
def test(idx, queue):
    results = []
    level1_init(results, queue)
    # just to be sure that it is possible to pass empty list
    queue.progress([])
    while queue.__futures__:
        task = queue.__futures__[idx]
        task.run()
        queue.progress([task])
    assert results == SCRIPT
    assert not queue._futures
    assert not queue._forks
    assert not queue._callbacks
