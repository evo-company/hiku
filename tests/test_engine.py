from __future__ import unicode_literals

from concurrent.futures import ThreadPoolExecutor

from hiku import query
from hiku.graph import Edge, Field, Link
from hiku.engine import Engine
from hiku.readers.simple import read
from hiku.executors.threads import ThreadsExecutor

from .base import TestCase, patch, reqs_eq_patcher


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
        self.engine = Engine(ThreadsExecutor(thread_pool))

    def execute(self, query):
        return self.engine.execute(TEST_ENV, read(query))

    def testFields(self):
        with _patch(query_fields1) as qf1, _patch(query_fields2) as qf2:
            qf1.return_value = ['a1']
            qf2.return_value = ['b1']
            self.assertResult(self.execute('[:a :b]'), {'a': 'a1', 'b': 'b1'})
            with reqs_eq_patcher():
                qf1.assert_called_once_with([query.Field('a')])
                qf2.assert_called_once_with([query.Field('b')])

    def testEdgeFields(self):
        with _patch(query_fields1) as qf1, _patch(query_fields2) as qf2:
            qf1.return_value = ['d1']
            qf2.return_value = ['e1']
            self.assertResult(self.execute('[{:c [:d :e]}]'),
                              {'c': {'d': 'd1', 'e': 'e1'}})
            with reqs_eq_patcher():
                qf1.assert_called_once_with([query.Field('d')])
                qf2.assert_called_once_with([query.Field('e')])

    def testLinkFields(self):
        with _patch(query_fields1) as qf1, _patch(query_fields2) as qf2,\
                _patch(query_link1) as ql1:
            ql1.return_value = [1]
            qf1.return_value = [['d1']]
            qf2.return_value = [['e1']]
            result = self.execute('[{:f [:d :e]}]')
            self.assertResult(result, {'f': [{'d': 'd1', 'e': 'e1'}]})
            self.assertEqual(result.idx, {'c': {1: {'d': 'd1', 'e': 'e1'}}})
            with reqs_eq_patcher():
                ql1.assert_called_once_with()
                qf1.assert_called_once_with([query.Field('d')], [1])
                qf2.assert_called_once_with([query.Field('e')], [1])

    def testLinks(self):
        with _patch(query_fields1) as qf1, _patch(query_fields2) as qf2,\
                _patch(query_link1) as ql1, _patch(query_link2) as ql2:
            ql1.return_value = [1]
            qf1.return_value = [['d1']]
            ql2.return_value = [2]
            qf2.return_value = [['e1']]
            result = self.execute('[{:f [:d]} {:g [:e]}]')
            self.assertResult(result, {'f': [{'d': 'd1'}], 'g': [{'e': 'e1'}]})
            self.assertEqual(result.idx, {'c': {1: {'d': 'd1'},
                                                2: {'e': 'e1'}}})
            with reqs_eq_patcher():
                ql1.assert_called_once_with()
                qf1.assert_called_once_with([query.Field('d')], [1])
                ql2.assert_called_once_with()
                qf2.assert_called_once_with([query.Field('e')], [2])

    def testFieldOptions(self):
        with _patch(query_fields1) as qf1:
            qf1.return_value = ['a1']
            result = self.execute('[(:a :foo "bar")]')
            self.assertResult(result, {'a': 'a1'})
            with reqs_eq_patcher():
                qf1.assert_called_once_with([
                    query.Field('a', options={'foo': 'bar'}),
                ])

    @patch.object(TEST_ENV.fields['f'], 'options', {'foo'})
    def testLinkOptions(self):
        with _patch(query_link1) as ql1, _patch(query_fields1) as qf1:
            ql1.return_value = [1]
            qf1.return_value = [['d1']]
            result = self.execute('[{(:f :foo "bar") [:d]}]')
            self.assertResult(result, {'f': [{'d': 'd1'}]})
            with reqs_eq_patcher():
                ql1.assert_called_once_with({'foo': 'bar'})
                qf1.assert_called_once_with([query.Field('d')], [1])
