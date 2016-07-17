from hiku.graph import Graph, Edge, Field, Root, Link, Option, MANY
from hiku.validate.graph import GraphValidator


def _fields_func(fields, ids):
    pass


def _link_func(ids):
    pass


def check_errors(graph, errors):
    validator = GraphValidator(graph)
    validator.visit(graph)
    assert validator.errors.list == errors


def test_graph_contain_duplicate_edges():
    check_errors(
        Graph([
            Edge('foo', []),
            Edge('foo', []),
        ]),
        ['Duplicated edge names found in the graph: "foo"'],
    )


def test_graph_contain_invalid_types():
    check_errors(
        Graph([
            1,
            Edge('foo', []),
        ]),
        [('Graph can not contain these types: {!r}'
          .format(int))],
    )


def test_edge_contain_duplicate_fields():
    check_errors(
        Graph([
            Root([
                Field('b', _fields_func),
            ]),
            Edge('foo', [
                Field('a', _fields_func),
                Field('a', _fields_func),
            ]),
            Root([
                Field('b', _fields_func),
            ]),
        ]),
        ['Duplicated names found in the "root" edge: "b"',
         'Duplicated names found in the "foo" edge: "a"'],
    )


def test_edge_contain_edge():
    check_errors(
        Graph([
            Root([
                # this is ok
                Edge('foo', []),
            ]),
            Edge('bar', [
                # this is wrong
                Edge('baz', []),
            ]),
        ]),
        ['Edge can not be defined in the non-root edge: "baz" in "bar"'],
    )


def test_edge_contain_invalid_types():
    check_errors(
        Graph([
            Edge('foo', [
                1,
                Field('bar', _fields_func),
            ]),
        ]),
        [('Edge can not contain these types: {!r} in edge "foo"'
          .format(int))],
    )


def test_link_missing_edge():
    check_errors(
        Graph([
            Edge('bar', [
                Link('link', MANY, _link_func, edge='missing', requires=None),
            ]),
        ]),
        ['Link "bar.link" points to the missing edge "missing"'],
    )


def test_link_requires_missing_field():
    check_errors(
        Graph([
            Edge('foo', []),
            Edge('bar', [
                Link('link1', MANY, _link_func, edge='foo',
                     requires='missing1'),
            ]),
            Root([
                Link('link2', MANY, _link_func, edge='foo',
                     requires='missing2'),
            ]),
        ]),
        ['Link "link2" requires missing field "missing2" in the "root" edge',
         'Link "link1" requires missing field "missing1" in the "bar" edge'],
    )


def test_link_contain_invalid_types():
    check_errors(
        Graph([
            Edge('foo', []),
            Edge('bar', [
                Field('id', _fields_func),
                Link('baz', MANY, _link_func, edge='foo', requires='id',
                     options=[Option('size'), 1]),
            ]),
        ]),
        [('Invalid types provided as link "bar.baz" options: {!r}'
          .format(int))],
    )
