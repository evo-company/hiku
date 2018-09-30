import re

import pytest

from hiku import query as q
from hiku.graph import Graph, Node, Field, Link, Option, Root
from hiku.types import Record, Sequence, Integer, Optional, TypeRef
from hiku.utils import listify
from hiku.engine import Engine, pass_context, Context
from hiku.builder import build, Q
from hiku.executors.sync import SyncExecutor

from .base import check_result, ANY, Mock


@listify
def id_field(fields, ids):
    for i in ids:
        yield [i for _ in fields]


OPTION_BEHAVIOUR = [
    (Option('op', None), {'op': 1812}, {'op': 1812}),
    (Option('op', None, default=None), {}, {'op': None}),
    (Option('op', None, default=None), {'op': 2340}, {'op': 2340}),
    (Option('op', None, default=3914), {}, {'op': 3914}),
    (Option('op', None, default=4254), {'op': None}, {'op': None}),
    (Option('op', None, default=1527), {'op': 8361}, {'op': 8361}),
]


def execute(graph, query_, ctx=None):
    engine = Engine(SyncExecutor())
    return engine.execute(graph, query_, ctx=ctx)


def test_root_fields():
    f1 = Mock(return_value=['boiardo'])
    f2 = Mock(return_value=['isolde'])

    graph = Graph([
        Root([
            Field('a', None, f1),
            Field('b', None, f2),
        ]),
    ])

    result = execute(graph, build([Q.a, Q.b]))
    check_result(result, {'a': 'boiardo', 'b': 'isolde'})

    f1.assert_called_once_with([q.Field('a')])
    f2.assert_called_once_with([q.Field('b')])


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

    result = execute(graph, build([Q.d[Q.b, Q.c]]))
    check_result(result, {'d': [{'b': 'harkis', 'c': 'slits'}]})

    f1.assert_called_once_with()
    f2.assert_called_once_with([q.Field('b')], [1])
    f3.assert_called_once_with([q.Field('c')], [1])


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
        execute(graph, build([Q.e[Q.b[Q.f], Q.c[Q.g], Q.d[Q.h]]])),
        {'e': [{'b': {'f': 'marshes'},
                'c': {'g': 'colline'},
                'd': [{'h': 'magi'}]}]},
    )

    f1.assert_called_once_with()
    f2.assert_called_once_with(
        [q.Link('b', q.Node([q.Field('f')]))], [1],
    )
    f3.assert_called_once_with(
        [q.Link('c', q.Node([q.Field('g')]))], [1],
    )
    f4.assert_called_once_with(
        [q.Link('d', q.Node([q.Field('h')]))], [1],
    )


def test_links():
    fb = Mock(return_value=[1])
    fc = Mock(return_value=[2])
    fi = Mock(return_value=[3])
    fd = Mock(return_value=[['boners']])
    fe = Mock(return_value=[['julio']])

    graph = Graph([
        Node('a', [
            Field('d', None, fd),
            Field('e', None, fe),
        ]),
        Root([
            Field('i', None, fi),
            Link('b', Sequence[TypeRef['a']], fb, requires=None),
            Link('c', Sequence[TypeRef['a']], fc, requires='i'),
        ]),
    ])

    result = execute(graph, build([Q.b[Q.d], Q.c[Q.e]]))
    check_result(result, {'b': [{'d': 'boners'}],
                          'c': [{'e': 'julio'}]})

    fi.assert_called_once_with([q.Field('i')])
    fb.assert_called_once_with()
    fc.assert_called_once_with(3)
    fd.assert_called_once_with([q.Field('d')], [1])
    fe.assert_called_once_with([q.Field('e')], [2])


@pytest.mark.parametrize('option, args, result', OPTION_BEHAVIOUR)
def test_field_option_valid(option, args, result):
    f = Mock(return_value=['baking'])
    graph = Graph([
        Root([
            Field('auslese', None, f, options=[option]),
        ]),
    ])
    check_result(execute(graph, build([Q.auslese(**args)])),
                 {'auslese': 'baking'})
    f.assert_called_once_with([q.Field('auslese', options=result)])


def test_field_option_unknown():
    test_field_option_valid(
        Option('inked', None), {'inked': 2340, 'unknown': 8775}, {'inked': 2340}
    )


def test_field_option_missing():
    graph = Graph([
        Root([
            Field('poofy', None, Mock(), options=[Option('mohism', None)]),
        ]),
    ])
    with pytest.raises(TypeError) as err:
        execute(graph, build([Q.poofy]))
    err.match('^Required option "mohism" for Field\(\'poofy\', '
              '(.*) was not provided$')


@pytest.mark.parametrize('option, args, result', OPTION_BEHAVIOUR)
def test_link_option_valid(option, args, result):
    f1 = Mock(return_value=[1])
    f2 = Mock(return_value=[['aunder']])
    graph = Graph([
        Node('a', [
            Field('c', None, f2),
        ]),
        Root([
            Link('b', Sequence[TypeRef['a']], f1, requires=None,
                 options=[option]),
        ]),
    ])
    check_result(execute(graph, build([Q.b(**args)[Q.c]])),
                 {'b': [{'c': 'aunder'}]})
    f1.assert_called_once_with(result)
    f2.assert_called_once_with([q.Field('c')], [1])


def test_link_option_unknown():
    test_link_option_valid(
        Option('oleic', None), {'oleic': 2340, 'unknown': 8775}, {'oleic': 2340}
    )


def test_link_option_missing():
    graph = Graph([
        Node('slices', [
            Field('papeete', None, Mock()),
        ]),
        Root([
            Link('eclairs', Sequence[TypeRef['slices']], Mock(), requires=None,
                 options=[Option('nocks', None)]),
        ]),
    ])
    with pytest.raises(TypeError) as err:
        execute(graph, build([Q.eclairs[Q.papeete]]))
    err.match('^Required option "nocks" for Link\(\'eclairs\', '
              '(.*) was not provided$')


def test_pass_context_field():
    f = pass_context(Mock(return_value=['boiardo']))

    graph = Graph([
        Root([
            Field('a', None, f),
        ]),
    ])

    check_result(execute(graph, build([Q.a]), {'vetch': 'shadier'}),
                 {'a': 'boiardo'})

    f.assert_called_once_with(ANY, [q.Field('a')])

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

    result = execute(graph, build([Q.c[Q.b]]), {'fibs': 'dossil'})
    check_result(result, {'c': [{'b': 'boners'}]})

    f1.assert_called_once_with(ANY)
    f2.assert_called_once_with([q.Field('b')], [1])

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

    result = execute(graph, build([Q.e[Q.d[Q.c]]]))
    check_result(result, {'e': [{'d': [{'c': 'arnhild'}]}]})

    f1.assert_called_once_with()
    f2.assert_called_once_with()
    f3.assert_called_once_with([q.Field('c')], [2])


@pytest.mark.parametrize('value', [1, [], [1, 2]])
def test_root_field_func_result_validation(value):
    with pytest.raises(TypeError) as err:
        execute(
            Graph([
                Root([
                    Field('a', None, Mock(return_value=value)),
                ]),
            ]),
            build([Q.a]),
        )
    err.match(re.escape(
        "Can't store field values, node: '__root__', fields: ['a'], "
        "expected: list (len: 1), returned: {value!r}"
        .format(value=value)
    ))


@pytest.mark.parametrize('value', [1, [], [1, 2], [[], []], [[1], []],
                                   [[], [2]]])
def test_node_field_func_result_validation(value):
    with pytest.raises(TypeError) as err:
        execute(
            Graph([
                Node('a', [
                    Field('b', None, Mock(return_value=value)),
                ]),
                Root([
                    Link('c', Sequence[TypeRef['a']], Mock(return_value=[1, 2]),
                         requires=None),
                ]),
            ]),
            build([Q.c[Q.b]]),
        )
    err.match(re.escape(
        "Can't store field values, node: 'a', fields: ['b'], "
        "expected: list (len: 2) of lists (len: 1), returned: {value!r}"
        .format(value=value)
    ))


def test_root_link_many_func_result_validation():
    with pytest.raises(TypeError) as err:
        execute(
            Graph([
                Node('a', [
                    Field('b', None, Mock(return_value=[[3], [4]])),
                ]),
                Root([
                    Link('c', Sequence[TypeRef['a']], Mock(return_value=123),
                         requires=None),
                ]),
            ]),
            build([Q.c[Q.b]]),
        )
    err.match(re.escape(
        "Can't store link values, node: '__root__', link: 'c', "
        "expected: list, returned: 123"
    ))


@pytest.mark.parametrize('value', [1, [], [1, 2, 3]])
def test_node_link_one_func_result_validation(value):
    with pytest.raises(TypeError) as err:
        execute(
            Graph([
                Node('a', [
                    Field('b', None, Mock(return_value=[[1], [2]]))
                ]),
                Node('c', [
                    Field('d', None, Mock(return_value=[[3], [4]])),
                    Link('e', TypeRef['a'], Mock(return_value=value),
                         requires='d'),
                ]),
                Root([
                    Link('f', Sequence[TypeRef['c']], Mock(return_value=[1, 2]),
                         requires=None),
                ]),
            ]),
            build([Q.f[Q.e[Q.b]]]),
        )
    err.match(re.escape(
        "Can't store link values, node: 'c', link: 'e', expected: "
        "list (len: 2), returned: {!r}".format(value)
    ))


@pytest.mark.parametrize('value', [1, [], [1, []], [[], 2], [[], [], []]])
def test_node_link_many_func_result_validation(value):
    with pytest.raises(TypeError) as err:
        execute(
            Graph([
                Node('a', [
                    Field('b', None, Mock(return_value=[[1], [2]]))
                ]),
                Node('c', [
                    Field('d', None, Mock(return_value=[[3], [4]])),
                    Link('e', Sequence[TypeRef['a']], Mock(return_value=value),
                         requires='d'),
                ]),
                Root([
                    Link('f', Sequence[TypeRef['c']], Mock(return_value=[1, 2]),
                         requires=None),
                ]),
            ]),
            build([Q.f[Q.e[Q.b]]]),
        )
    err.match(re.escape(
        "Can't store link values, node: 'c', link: 'e', expected: "
        "list (len: 2) of lists, returned: {!r}".format(value)
    ))


def test_root_field_alias():
    data = {'a': 42}

    def root_fields(fields):
        return [data[f.name] for f in fields]

    graph = Graph([
        Root([
            Field('a', None, root_fields),
        ]),
    ])
    result = execute(graph, q.Node([
        q.Field('a', alias='a1'),
        q.Field('a', alias='a2'),
    ]))
    check_result(result, {'a1': 42, 'a2': 42})


def test_node_field_alias():
    data = {'x1': {'a': 42}}

    @listify
    def x_fields(fields, ids):
        for i in ids:
            yield [data[i][f.name] for f in fields]

    graph = Graph([
        Node('X', [
            Field('a', None, x_fields),
        ]),
        Root([
            Link('x', TypeRef['X'], lambda: 'x1', requires=None),
        ]),
    ])
    result = execute(graph, q.Node([
        q.Link('x', q.Node([
            q.Field('a', alias='a1'),
            q.Field('a', alias='a2'),
        ])),
    ]))
    check_result(result, {'x': {'a1': 42, 'a2': 42}})


def test_root_link_alias():
    data = {
        'xN': {'a': 1, 'b': 2},
    }

    @listify
    def x_fields(fields, ids):
        for i in ids:
            yield [data[i][f.name] for f in fields]

    graph = Graph([
        Node('X', [
            Field('a', None, x_fields),
            Field('b', None, x_fields),
        ]),
        Root([
            Link('x', TypeRef['X'], lambda: 'xN', requires=None),
        ]),
    ])
    result = execute(graph, q.Node([
        q.Link('x', q.Node([q.Field('a')]), alias='x1'),
        q.Link('x', q.Node([q.Field('b')]), alias='x2'),
    ]))
    check_result(result, {
        'x1': {'a': 1},
        'x2': {'b': 2},
    })


def test_node_link_alias():
    data = {
        'yN': {'a': 1, 'b': 2},
    }
    x2y = {'xN': 'yN'}

    @listify
    def y_fields(fields, ids):
        for i in ids:
            yield [data[i][f.name] for f in fields]

    graph = Graph([
        Node('Y', [
            Field('a', None, y_fields),
            Field('b', None, y_fields),
        ]),
        Node('X', [
            Field('id', None, id_field),
            Link('y', TypeRef['Y'],
                 lambda ids: [x2y[i] for i in ids],
                 requires='id'),
        ]),
        Root([
            Link('x', TypeRef['X'], lambda: 'xN', requires=None),
        ]),
    ])
    result = execute(graph, q.Node([
        q.Link('x', q.Node([
            q.Link('y', q.Node([q.Field('a')]), alias='y1'),
            q.Link('y', q.Node([q.Field('b')]), alias='y2'),
        ])),
    ]))
    check_result(result, {
        'x': {
            'y1': {'a': 1},
            'y2': {'b': 2},
        }
    })


def test_conflicting_fields():
    x_data = {'xN': {'a': 42}}

    @listify
    def x_fields(fields, ids):
        for i in ids:
            yield ['{}-{}'.format(x_data[i][f.name], f.options['k'])
                   for f in fields]

    graph = Graph([
        Node('X', [
            Field('a', None, x_fields, options=[Option('k', Integer)]),
        ]),
        Root([
            Link('x1', TypeRef['X'], lambda: 'xN', requires=None),
            Link('x2', TypeRef['X'], lambda: 'xN', requires=None),
        ]),
    ])

    result = execute(graph, q.Node([
        q.Link('x1', q.Node([q.Field('a', options={'k': 1})])),
        q.Link('x2', q.Node([q.Field('a', options={'k': 2})])),
    ]))
    check_result(result, {
        'x1': {'a': '42-1'},
        'x2': {'a': '42-2'},
    })


def test_conflicting_links():
    data = {
        'yA': {'a': 1, 'b': 2},
        'yB': {'a': 3, 'b': 4},
        'yC': {'a': 5, 'b': 6},
    }
    x2y = {'xN': ['yA', 'yB', 'yC']}

    @listify
    def y_fields(fields, ids):
        for i in ids:
            yield [data[i][f.name] for f in fields]

    @listify
    def x_to_y_link(ids, options):
        for i in ids:
            yield [y for y in x2y[i] if y not in options['exclude']]

    graph = Graph([
        Node('Y', [
            Field('a', None, y_fields),
            Field('b', None, y_fields),
        ]),
        Node('X', [
            Field('id', None, id_field),
            Link('y', Sequence[TypeRef['Y']], x_to_y_link, requires='id',
                 options=[Option('exclude', None)]),
        ]),
        Root([
            Link('x1', TypeRef['X'], lambda: 'xN', requires=None),
            Link('x2', TypeRef['X'], lambda: 'xN', requires=None),
        ]),
    ])
    result = execute(graph, q.Node([
        q.Link('x1', q.Node([
            q.Link('y', q.Node([q.Field('a')]),
                   options={'exclude': ['yA']}),
        ])),
        q.Link('x2', q.Node([
            q.Link('y', q.Node([q.Field('b')]),
                   options={'exclude': ['yC']}),
        ])),
    ]))
    check_result(result, {
        'x1': {'y': [{'a': 3}, {'a': 5}]},
        'x2': {'y': [{'b': 2}, {'b': 4}]},
    })


def test_process_ordered_node():
    ordering = []

    def f1(fields):
        names = tuple(f.name for f in fields)
        ordering.append(names)
        return names

    def f2(fields):
        return f1(fields)

    def f3():
        ordering.append('x1')
        return 'x1'

    @listify
    def f4(fields, ids):
        for i in ids:
            yield ['{}-e'.format(i) for _ in fields]

    graph = Graph([
        Node('X', [
            Field('e', None, f4),
        ]),
        Root([
            Field('a', None, f1),
            Field('b', None, f1),
            Field('c', None, f2),
            Field('d', None, f2),
            Link('x', TypeRef['X'], f3, requires=None),
        ]),
    ])
    query = q.Node([
        q.Field('d'),
        q.Field('b'),
        q.Field('a'),
        q.Link('x', q.Node([
            q.Field('e'),
        ])),
        q.Field('c'),
    ], ordered=True)

    engine = Engine(SyncExecutor())
    result = engine.execute(graph, query)
    check_result(result, {
        'a': 'a',
        'b': 'b',
        'c': 'c',
        'd': 'd',
        'x': {
            'e': 'x1-e',
        },
    })
    assert ordering == [('d',), ('b', 'a'), 'x1', ('c',)]
