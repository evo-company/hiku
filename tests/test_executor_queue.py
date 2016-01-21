from hiku.executors.queue import Queue

from .base import TestCase


unknown = object()


class DummyFuture(object):

    def __init__(self, fn, args, kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.fn(*self.args, **self.kwargs)


class DummyExecutor(object):

    def submit(self, fn, *args, **kwargs):
        return DummyFuture(fn, args, kwargs)


def log_call(fn):
    def wrapper(self, *args, **kwargs):
        self.results.append('-> {}'.format(fn.__name__))
        res = fn(self, *args, **kwargs)
        self.results.append('<- {}'.format(fn.__name__))
        return res
    return wrapper


class TestQueue(TestCase):
    SCRIPT = [
        '-> level1_init',
        '<- level1_init',

        '.. level1_task1',
        '-> level1_task1_callback',
        '-> level2_init',
        '<- level2_init',
        '<- level1_task1_callback',

        '.. level2_task1',
        '-> level2_task1_callback',
        '-> level3_init',
        '<- level3_init',
        '<- level2_task1_callback',

        '.. level3_task1',
        '-> level3_task1_callback',
        '<- level3_task1_callback',

        '.. level3_task2',
        '-> level3_task2_callback',
        '<- level3_task2_callback',
        '-> level2_task_set3_callback',
        '<- level2_task_set3_callback',

        '.. level2_task2',
        '-> level2_task2_callback',
        '<- level2_task2_callback',
        '-> level1_task_set2_callback',
        '<- level1_task_set2_callback',

        '.. level1_task2',
        '-> level1_task2_callback',
        '<- level1_task2_callback',
        '-> level0_task_set1_callback',
        '<- level0_task_set1_callback',
    ]

    def func(self, arg):
        self.results.append('.. {}'.format(arg))

    @log_call
    def level1_init(self):
        self.task_set1 = self.queue.fork(None)
        level1_task1 = self.task_set1.submit(self.func, 'level1_task1')
        self.queue.add_callback(level1_task1, self.level1_task1_callback)
        self.queue.add_callback(self.task_set1, self.level0_task_set1_callback)

    @log_call
    def level1_task1_callback(self):
        self.level2_init()

    @log_call
    def level2_init(self):
        self.task_set2 = self.queue.fork(self.task_set1)
        level2_task1 = self.task_set2.submit(self.func, 'level2_task1')
        self.queue.add_callback(level2_task1, self.level2_task1_callback)
        self.queue.add_callback(self.task_set2, self.level1_task_set2_callback)

    @log_call
    def level2_task1_callback(self):
        self.level3_init()

    @log_call
    def level3_init(self):
        self.task_set3 = self.queue.fork(self.task_set2)
        level3_task1 = self.task_set3.submit(self.func, 'level3_task1')
        self.queue.add_callback(level3_task1, self.level3_task1_callback)
        self.queue.add_callback(self.task_set3, self.level2_task_set3_callback)

    @log_call
    def level3_task1_callback(self):
        level3_task2 = self.task_set3.submit(self.func, 'level3_task2')
        self.queue.add_callback(level3_task2, self.level3_task2_callback)

    @log_call
    def level3_task2_callback(self):
        pass

    @log_call
    def level2_task_set3_callback(self):
        level2_task2 = self.task_set2.submit(self.func, 'level2_task2')
        self.queue.add_callback(level2_task2, self.level2_task2_callback)

    @log_call
    def level2_task2_callback(self):
        pass

    @log_call
    def level1_task_set2_callback(self):
        level1_task2 = self.task_set1.submit(self.func, 'level1_task2')
        self.queue.add_callback(level1_task2, self.level1_task2_callback)

    @log_call
    def level1_task2_callback(self):
        pass

    @log_call
    def level0_task_set1_callback(self):
        pass

    def setUp(self):
        self.executor = DummyExecutor()
        self.queue = Queue(self.executor)
        self.results = []
        self.maxDiff = None

    def _test(self, idx):
        self.level1_init()
        # just to be sure that it is possible to pass empty list
        self.queue.progress([])
        while self.queue.__futures__:
            task = self.queue.__futures__[idx]
            task.run()
            self.queue.progress([task])
        self.assertEqual(self.results, self.SCRIPT)
        self.assertFalse(self.queue._futures)
        self.assertFalse(self.queue._forks)
        self.assertFalse(self.queue._callbacks)

    def testForward(self):
        self._test(0)

    def testBackward(self):
        self._test(-1)
