from __future__ import unicode_literals

from concurrent.futures import ThreadPoolExecutor

from hiku.graph import Edge, Field, Link
from hiku.engine import Engine
from hiku.readers.simple import read
from hiku.executors.thread import ThreadExecutor

from .base import TestCase, patch


def query_fields1(*args, **kwargs):
    pass


def query_fields2(*args, **kwargs):
    pass


def query_link1(*args, **kwargs):
    pass


def query_link2(*args, **kwargs):
    pass


def _(func):
    def wrapper(*args, **kwargs):
        return globals()[func.__name__](*args, **kwargs)
    return wrapper


def _patch(func):
    return patch('{}.{}'.format(__name__, func.__name__))


TEST_ENV = Edge(None, [
    Field('a', _(query_fields1)),
    Field('b', _(query_fields2)),
    Edge('c', [
        Field('d', _(query_fields1)),
        Field('e', _(query_fields2)),
    ]),
    Link('f', None, 'c', _(query_link1), to_list=True),
    Link('g', None, 'c', _(query_link2), to_list=True),
])

thread_pool = ThreadPoolExecutor(2)


class TestEngine(TestCase):

    def setUp(self):
        self.engine = Engine(ThreadExecutor(thread_pool))

    def execute(self, query):
        return self.engine.execute(TEST_ENV, read(query))

    def testFields(self):
        with _patch(query_fields1) as qf1, _patch(query_fields2) as qf2:
            qf1.return_value = ['a1']
            qf2.return_value = ['b1']
            self.assertResult(self.execute('[:a :b]'), {'a': 'a1', 'b': 'b1'})
            qf1.assert_called_once_with(['a'])
            qf2.assert_called_once_with(['b'])

    def testEdgeFields(self):
        with _patch(query_fields1) as qf1, _patch(query_fields2) as qf2:
            qf1.return_value = ['d1']
            qf2.return_value = ['e1']
            self.assertResult(self.execute('[{:c [:d :e]}]'),
                              {'c': {'d': 'd1', 'e': 'e1'}})
            qf1.assert_called_once_with(['d'])
            qf2.assert_called_once_with(['e'])

    def testLinkFields(self):
        with _patch(query_fields1) as qf1, _patch(query_fields2) as qf2,\
                _patch(query_link1) as ql1:
            ql1.return_value = [1]
            qf1.return_value = [['d1']]
            qf2.return_value = [['e1']]
            store = self.execute('[{:f [:d :e]}]')
            self.assertResult(store, {'f': [{'d': 'd1', 'e': 'e1'}]})
            self.assertEqual(store.idx, {'c': {1: {'d': 'd1', 'e': 'e1'}}})
            ql1.assert_called_once_with()
            qf1.assert_called_once_with(['d'], [1])
            qf2.assert_called_once_with(['e'], [1])

    def testLinks(self):
        with _patch(query_fields1) as qf1, _patch(query_fields2) as qf2,\
                _patch(query_link1) as ql1, _patch(query_link2) as ql2:
            ql1.return_value = [1]
            qf1.return_value = [['d1']]
            ql2.return_value = [2]
            qf2.return_value = [['e1']]
            store = self.execute('[{:f [:d]} {:g [:e]}]')
            self.assertResult(store, {'f': [{'d': 'd1'}], 'g': [{'e': 'e1'}]})
            self.assertEqual(store.idx, {'c': {1: {'d': 'd1'}, 2: {'e': 'e1'}}})
            ql1.assert_called_once_with()
            qf1.assert_called_once_with(['d'], [1])
            ql2.assert_called_once_with()
            qf2.assert_called_once_with(['e'], [2])
