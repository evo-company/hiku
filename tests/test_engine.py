from __future__ import unicode_literals

from unittest import TestCase, skip
from concurrent.futures import ThreadPoolExecutor

from hiku.graph import Edge, Field
from hiku.engine import Engine
from hiku.readers.simple import read
from hiku.executors.thread import ThreadExecutor

from .base import patch


def query_fields(*args, **kwargs):
    pass


def _(func):
    def wrapper(*args, **kwargs):
        return globals()[func.__name__](*args, **kwargs)
    return wrapper


def _patch(func):
    return patch('{}.{}'.format(__name__, func.__name__))


TEST_ENV = Edge(None, [
    Field('a', _(query_fields)),
    Edge('b', [
        Field('c', _(query_fields)),
    ]),
])

thread_pool = ThreadPoolExecutor(2)


class TestEngine(TestCase):

    def setUp(self):
        self.engine = Engine(ThreadExecutor(thread_pool))

    def execute(self, query):
        return self.engine.execute(TEST_ENV, read(query))

    def testField(self):
        with _patch(query_fields) as p:
            p.return_value = ['test']
            self.assertEqual(self.execute('[:a]'),
                             {'a': 'test'})
            p.assert_called_once_with(['a'])

    def testEdgeField(self):
        with _patch(query_fields) as p:
            p.return_value = ['test']
            self.assertEqual(self.execute('[{:b [:c]}]'),
                             {'b': {'c': 'test'}})
            p.assert_called_once_with(['c'])
