from __future__ import unicode_literals

import pytest

from hiku import query
from hiku.graph import Graph, Node, Field, Link, Option, Root
from hiku.types import Record, Sequence, Integer, Optional, TypeRef
from hiku.engine import Engine, pass_context, Context
from hiku.executors.sync import SyncExecutor
from hiku.readers.simple import read

from .base import reqs_eq_patcher, check_result, ANY, Mock


def execute(graph, query_, ctx=None):
    engine = Engine(SyncExecutor())
    return engine.execute(graph, read(query_), ctx=ctx)


def test_root_fields():
    f1 = Mock(return_value=['boiardo'])
    f2 = Mock(return_value=['isolde'])

    graph = Graph([
        Root([
            Field('a', None, f1),
            Field('b', None, f2),
        ]),
    ])

    result = execute(graph, '[:a :b]')
    check_result(result, {'a': 'boiardo', 'b': 'isolde'})

    with reqs_eq_patcher():
        f1.assert_called_once_with([query.Field('a')])
        f2.assert_called_once_with([query.Field('b')])


def test_root_node_fields():
    f1 = Mock(return_value=['khios'])
    f2 = Mock(return_value=['cambay'])

    graph = Graph([
        Root([
            Node('a', [
                Field('b', None, f1),
                Field('c', None, f2),
            ]),
        ]),
    ])

    result = execute(graph, '[{:a [:b :c]}]')
    check_result(result, {'a': {'b': 'khios', 'c': 'cambay'}})

    with reqs_eq_patcher():
        f1.assert_called_once_with([query.Field('b')])
        f2.assert_called_once_with([query.Field('c')])


def test_node_fields():
    f1 = Mock(return_value=[1])
    f2 = Mock(return_value=[['harkis']])
    f3 = Mock(return_value=[['slits']])

    graph = Graph([
        Node('a', [
            Field('b', None, f2),
            Field('c', None, f3),
        ]),
        Root([
            Link('d', Sequence[TypeRef['a']], f1, requires=None),
        ]),
    ])

    result = execute(graph, '[{:d [:b :c]}]')
    check_result(result, {'d': [{'b': 'harkis', 'c': 'slits'}]})
    assert result.index == {'a': {1: {'b': 'harkis', 'c': 'slits'}}}

    f1.assert_called_once_with()
    with reqs_eq_patcher():
        f2.assert_called_once_with([query.Field('b')], [1])
        f3.assert_called_once_with([query.Field('c')], [1])


def test_node_complex_fields():
    f1 = Mock(return_value=[1])
    f2 = Mock(return_value=[[{'f': 'marshes'}]])
    f3 = Mock(return_value=[[{'g': 'colline'}]])
    f4 = Mock(return_value=[[[{'h': 'magi'}]]])

    graph = Graph([
        Node('a', [
            Field('b', Optional[Record[{'f': Integer}]], f2),
            Field('c', Record[{'g': Integer}], f3),
            Field('d', Sequence[Record[{'h': Integer}]], f4),
        ]),
        Root([
            Link('e', Sequence[TypeRef['a']], f1, requires=None),
        ]),
    ])

    check_result(
        execute(graph, """
        [{:e [{:b [:f]} {:c [:g]} {:d [:h]}]}]
        """),
        {'e': [{'b': {'f': 'marshes'},
                'c': {'g': 'colline'},
                'd': [{'h': 'magi'}]}]},
    )

    f1.assert_called_once_with()
    with reqs_eq_patcher():
        f2.assert_called_once_with(
            [query.Link('b', query.Node([query.Field('f')]))], [1],
        )
        f3.assert_called_once_with(
            [query.Link('c', query.Node([query.Field('g')]))], [1],
        )
        f4.assert_called_once_with(
            [query.Link('d', query.Node([query.Field('h')]))], [1],
        )


def test_links():
    f1 = Mock(return_value=[1])
    f2 = Mock(return_value=[2])
    f3 = Mock(return_value=[['boners']])
    f4 = Mock(return_value=[['julio']])

    graph = Graph([
        Node('a', [
            Field('d', None, f3),
            Field('e', None, f4),
        ]),
        Root([
            Link('b', Sequence[TypeRef['a']], f1, requires=None),
            Link('c', Sequence[TypeRef['a']], f2, requires=None),
        ]),
    ])

    result = execute(graph, '[{:b [:d]} {:c [:e]}]')
    check_result(result, {'b': [{'d': 'boners'}],
                          'c': [{'e': 'julio'}]})
    assert result.index == {'a': {1: {'d': 'boners'},
                                  2: {'e': 'julio'}}}

    f1.assert_called_once_with()
    f2.assert_called_once_with()
    with reqs_eq_patcher():
        f3.assert_called_once_with([query.Field('d')], [1])
        f4.assert_called_once_with([query.Field('e')], [2])


def test_field_options():
    f = Mock(return_value=['baking'])

    graph = Graph([
        Root([
            Field('a', None, f),
        ]),
    ])

    # FIXME: options should be defined and validated
    check_result(execute(graph, '[(:a {:b "bubkus"})]'),
                 {'a': 'baking'})

    with reqs_eq_patcher():
        f.assert_called_once_with([
            query.Field('a', options={'b': 'bubkus'}),
        ])


def test_link_option():
    f1 = Mock(return_value=[1])
    f2 = Mock(return_value=[['aunder']])

    graph = Graph([
        Node('a', [
            Field('c', None, f2),
        ]),
        Root([
            Link('b', Sequence[TypeRef['a']], f1, requires=None,
                 options=[Option('d', None)]),
        ]),
    ])

    check_result(execute(graph, '[{(:b {:d "duncery"}) [:c]}]'),
                 {'b': [{'c': 'aunder'}]})

    f1.assert_called_once_with({'d': 'duncery'})
    with reqs_eq_patcher():
        f2.assert_called_once_with([query.Field('c')], [1])


def test_link_option_missing():
    f = Mock()

    graph = Graph([
        Node('a', [
            Field('d', None, f),
        ]),
        Root([
            Link('b', Sequence[TypeRef['a']], f, requires=None,
                 options=[Option('d', None)]),
        ]),
    ])

    with pytest.raises(TypeError) as err:
        execute(graph, '[{:b [:d]}]')
    err.match('^Required option "d" for (.*)b(.*) was not provided$')


def test_link_option_default_none():
    f1 = Mock(return_value=[1])
    f2 = Mock(return_value=[['kaitlin']])

    graph = Graph([
        Node('a', [
            Field('c', None, f2),
        ]),
        Root([
            Link('b', Sequence[TypeRef['a']], f1, requires=None,
                 options=[Option('d', None, default=None)]),
        ]),
    ])

    check_result(execute(graph, '[{:b [:c]}]'),
                 {'b': [{'c': 'kaitlin'}]})

    f1.assert_called_once_with({'d': None})
    with reqs_eq_patcher():
        f2.assert_called_once_with([query.Field('c')], [1])


def test_link_option_default_string():
    f1 = Mock(return_value=[1])
    f2 = Mock(return_value=[['rounded']])

    graph = Graph([
        Node('a', [
            Field('c', None, f2),
        ]),
        Root([
            Link('b', Sequence[TypeRef['a']], f1, requires=None,
                 options=[Option('d', None, default='reaving')]),
        ]),
    ])

    check_result(execute(graph, '[{:b [:c]}]'),
                 {'b': [{'c': 'rounded'}]})

    f1.assert_called_once_with({'d': 'reaving'})
    with reqs_eq_patcher():
        f2.assert_called_once_with([query.Field('c')], [1])


def test_link_option_unknown():
    f1 = Mock(return_value=[1])
    f2 = Mock(return_value=[['tarweed']])

    graph = Graph([
        Node('a', [
            Field('c', None, f2),
        ]),
        Root([
            Link('b', Sequence[TypeRef['a']], f1, requires=None,
                 options=[Option('d', None, default='gerry')]),
        ]),
    ])

    result = execute(graph, '[{(:b {:d "hanna" :unknown "linty"}) [:c]}]')
    check_result(result, {'b': [{'c': 'tarweed'}]})

    f1.assert_called_once_with({'d': 'hanna'})
    with reqs_eq_patcher():
        f2.assert_called_once_with([query.Field('c')], [1])


def test_pass_context_field():
    f = pass_context(Mock(return_value=['boiardo']))

    graph = Graph([
        Root([
            Field('a', None, f),
        ]),
    ])

    check_result(execute(graph, '[:a]', {'vetch': 'shadier'}),
                 {'a': 'boiardo'})

    with reqs_eq_patcher():
        f.assert_called_once_with(ANY, [query.Field('a')])

    ctx = f.call_args[0][0]
    assert isinstance(ctx, Context)
    assert ctx['vetch'] == 'shadier'
    with pytest.raises(KeyError) as err:
        _ = ctx['invalid']  # noqa
    err.match('is not specified in the query context')


def test_pass_context_link():
    f1 = pass_context(Mock(return_value=[1]))
    f2 = Mock(return_value=[['boners']])

    graph = Graph([
        Node('a', [
            Field('b', None, f2),
        ]),
        Root([
            Link('c', Sequence[TypeRef['a']], f1, requires=None),
        ]),
    ])

    result = execute(graph, '[{:c [:b]}]', {'fibs': 'dossil'})
    check_result(result, {'c': [{'b': 'boners'}]})
    assert result.index == {'a': {1: {'b': 'boners'}}}

    f1.assert_called_once_with(ANY)
    with reqs_eq_patcher():
        f2.assert_called_once_with([query.Field('b')], [1])

    ctx = f1.call_args[0][0]
    assert isinstance(ctx, Context)
    assert ctx['fibs'] == 'dossil'
    with pytest.raises(KeyError) as err:
        _ = ctx['invalid']  # noqa
    err.match('is not specified in the query context')


def test_node_link_without_requirements():
    f1 = Mock(return_value=[1])
    f2 = Mock(return_value=[2])
    f3 = Mock(return_value=[['arnhild']])

    graph = Graph([
        Node('a', [
            Field('c', None, f3),
        ]),
        Node('b', [
            Link('d', Sequence[TypeRef['a']], f2, requires=None),
        ]),
        Root([
            Link('e', Sequence[TypeRef['b']], f1, requires=None),
        ]),
    ])

    result = execute(graph, '[{:e [{:d [:c]}]}]')
    check_result(result, {'e': [{'d': [{'c': 'arnhild'}]}]})
    assert result.index == {
        'a': {2: {'c': 'arnhild'}},
        'b': {1: {'d': [result.ref('a', 2)]}},
    }

    f1.assert_called_once_with()
    f2.assert_called_once_with()
    with reqs_eq_patcher():
        f3.assert_called_once_with([query.Field('c')], [2])
