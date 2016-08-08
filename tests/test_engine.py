from __future__ import unicode_literals

from concurrent.futures import ThreadPoolExecutor

from hiku import query
from hiku.graph import Graph, Edge, Field, Link, Option, Root, Many
from hiku.types import Record, Sequence, Integer, Optional
from hiku.engine import Engine
from hiku.readers.simple import read
from hiku.executors.threads import ThreadsExecutor

from .base import patch, reqs_eq_patcher, check_result


def query_fields1(*args, **kwargs):
    pass


def query_fields2(*args, **kwargs):
    pass


def query_fields3(*args, **kwargs):
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
    return patch('{}.{}'.format(__name__, getattr(func, '__name__')))


# TODO: refactor
TEST_ENV = Graph([
    Edge('c', [
        Field('d', _(query_fields1)),
        Field('e', _(query_fields2)),
        Field('struct_maybe', Optional[Record[{'f1': Integer}]],
              _(query_fields1)),
        Field('struct_one', Record[{'f2': Integer}],
              _(query_fields2)),
        Field('struct_many', Sequence[Record[{'f3': Integer}]],
              _(query_fields3)),
    ]),
    Root([
        Field('a', _(query_fields1)),
        Field('b', _(query_fields2)),
        Edge('c', [
            Field('d', _(query_fields1)),
            Field('e', _(query_fields2)),
        ]),
        Link('f', Many, _(query_link1), edge='c', requires=None),
        Link('g', Many, _(query_link2), edge='c', requires=None),
        Link('h', Many, _(query_link1), edge='c', requires=None,
             options=[Option('foo')]),
        Link('k', Many, _(query_link1), edge='c', requires=None,
             options=[Option('foo', default=1)]),
    ]),
])

thread_pool = ThreadPoolExecutor(2)


def execute(query_):
    engine = Engine(ThreadsExecutor(thread_pool))
    return engine.execute(TEST_ENV, read(query_))


def test_root_fields():
    with _patch(query_fields1) as qf1, _patch(query_fields2) as qf2:
        qf1.return_value = ['a1']
        qf2.return_value = ['b1']
        check_result(execute('[:a :b]'), {'a': 'a1', 'b': 'b1'})
        with reqs_eq_patcher():
            qf1.assert_called_once_with([query.Field('a')])
            qf2.assert_called_once_with([query.Field('b')])


def test_root_edge_fields():
    with _patch(query_fields1) as qf1, _patch(query_fields2) as qf2:
        qf1.return_value = ['d1']
        qf2.return_value = ['e1']
        check_result(execute('[{:c [:d :e]}]'),
                     {'c': {'d': 'd1', 'e': 'e1'}})
        with reqs_eq_patcher():
            qf1.assert_called_once_with([query.Field('d')])
            qf2.assert_called_once_with([query.Field('e')])


def test_edge_fields():
    with \
            _patch(query_fields1) as qf1,\
            _patch(query_fields2) as qf2,\
            _patch(query_link1) as ql1:

        ql1.return_value = [1]
        qf1.return_value = [['d1']]
        qf2.return_value = [['e1']]
        result = execute('[{:f [:d :e]}]')
        check_result(result, {'f': [{'d': 'd1', 'e': 'e1'}]})
        assert result.index == {'c': {1: {'d': 'd1', 'e': 'e1'}}}
        with reqs_eq_patcher():
            ql1.assert_called_once_with()
            qf1.assert_called_once_with([query.Field('d')], [1])
            qf2.assert_called_once_with([query.Field('e')], [1])


def test_edge_complex_fields():
    with \
            _patch(query_link1) as ql1,\
            _patch(query_fields1) as qf1,\
            _patch(query_fields2) as qf2,\
            _patch(query_fields3) as qf3:

        ql1.return_value = [1]
        qf1.return_value = [[{'f1': 'f1val'}]]
        qf2.return_value = [[{'f2': 'f2val'}]]
        qf3.return_value = [[[{'f3': 'f3val'}]]]

        check_result(
            execute(
                '[{:f [{:struct_maybe [:f1]} '
                '      {:struct_one [:f2]} '
                '      {:struct_many [:f3]}]}]'
            ),
            {'f': [{'struct_maybe': {'f1': 'f1val'},
                    'struct_one': {'f2': 'f2val'},
                    'struct_many': [{'f3': 'f3val'}]}]},
        )

        with reqs_eq_patcher():
            ql1.assert_called_once_with()
            qf1.assert_called_once_with([
                query.Link('struct_maybe',
                           query.Edge([query.Field('f1')]))],
                [1],
            )
            qf2.assert_called_once_with([
                query.Link('struct_one',
                           query.Edge([query.Field('f2')]))],
                [1],
            )
            qf3.assert_called_once_with([
                query.Link('struct_many',
                           query.Edge([query.Field('f3')]))],
                [1],
            )


def test_links():
    with \
            _patch(query_fields1) as qf1,\
            _patch(query_fields2) as qf2,\
            _patch(query_link1) as ql1,\
            _patch(query_link2) as ql2:

        ql1.return_value = [1]
        qf1.return_value = [['d1']]
        ql2.return_value = [2]
        qf2.return_value = [['e1']]
        result = execute('[{:f [:d]} {:g [:e]}]')
        check_result(result, {'f': [{'d': 'd1'}], 'g': [{'e': 'e1'}]})
        assert result.index == {'c': {1: {'d': 'd1'}, 2: {'e': 'e1'}}}
        with reqs_eq_patcher():
            ql1.assert_called_once_with()
            qf1.assert_called_once_with([query.Field('d')], [1])
            ql2.assert_called_once_with()
            qf2.assert_called_once_with([query.Field('e')], [2])


def test_field_options():
    with _patch(query_fields1) as qf1:
        qf1.return_value = ['a1']
        result = execute('[(:a {:foo "bar"})]')
        check_result(result, {'a': 'a1'})
        with reqs_eq_patcher():
            qf1.assert_called_once_with([
                query.Field('a', options={'foo': 'bar'}),
            ])


def test_link_option():
    with _patch(query_link1) as ql1, _patch(query_fields1) as qf1:
        ql1.return_value = [1]
        qf1.return_value = [['d1']]
        result = execute('[{(:h {:foo 5}) [:d]}]')
        check_result(result, {'h': [{'d': 'd1'}]})
        with reqs_eq_patcher():
            ql1.assert_called_once_with({'foo': 5})
            qf1.assert_called_once_with([query.Field('d')], [1])


def test_link_option_default():
    with _patch(query_link1) as ql1, _patch(query_fields1) as qf1:
        ql1.return_value = [1]
        qf1.return_value = [['d1']]
        result = execute('[{:k [:d]}]')
        check_result(result, {'k': [{'d': 'd1'}]})
        with reqs_eq_patcher():
            ql1.assert_called_once_with({'foo': 1})
            qf1.assert_called_once_with([query.Field('d')], [1])


def test_link_option_unknown():
    with _patch(query_link1) as ql1, _patch(query_fields1) as qf1:
        ql1.return_value = [1]
        qf1.return_value = [['d1']]
        result = execute('[{(:k {:foo 2 :bar 3}) [:d]}]')
        check_result(result, {'k': [{'d': 'd1'}]})
        with reqs_eq_patcher():
            ql1.assert_called_once_with({'foo': 2})
            qf1.assert_called_once_with([query.Field('d')], [1])
