import pytest

from hiku.graph import Graph, Node, Field, Root, Link, Option
from hiku.types import TypeRef, Sequence
from hiku.validate.graph import GraphValidationError


def _fields_func(fields, ids):
    pass


def _link_func(ids):
    pass


def check_errors(graph_items, errors):
    with pytest.raises(GraphValidationError) as err:
        Graph(graph_items)
    assert err.value.errors == errors


def test_graph_contain_duplicate_nodes():
    check_errors(
        [
            Node('foo', []),
            Node('foo', []),
        ],
        ['Duplicated nodes found in the graph: "foo"'],
    )


def test_graph_contain_invalid_types():
    check_errors(
        [
            1,
            Node('foo', []),
        ],
        [('Graph can not contain these types: {!r}'
          .format(int))],
    )


def test_node_contain_duplicate_fields():
    check_errors(
        [
            Root([
                Field('b', None, _fields_func),
            ]),
            Node('foo', [
                Field('a', None, _fields_func),
                Field('a', None, _fields_func),
            ]),
            Root([
                Field('b', None, _fields_func),
            ]),
        ],
        ['Duplicated names found in the "root" node: "b"',
         'Duplicated names found in the "foo" node: "a"'],
    )


def test_node_contain_node():
    check_errors(
        [
            Root([
                Node('foo', []),
            ]),
            Node('bar', [
                Node('baz', []),
            ]),
        ],
        [
            'Node can not contain these types: '
            '<class \'hiku.graph.Node\'> in node "root"',
            'Node can not contain these types: '
            '<class \'hiku.graph.Node\'> in node "bar"',
        ],
    )


def test_node_contain_invalid_types():
    check_errors(
        [
            Node('foo', [
                1,
                Field('bar', None, _fields_func),
            ]),
        ],
        [('Node can not contain these types: {!r} in node "foo"'
          .format(int))],
    )


def test_link_missing_node():
    check_errors(
        [
            Node('bar', [
                Link('link', Sequence[TypeRef['missing']],
                     _link_func, requires=None),
            ]),
        ],
        ['Link "bar.link" points to the missing node "missing"'],
    )


def test_link_requires_missing_field():
    check_errors(
        [
            Node('foo', []),
            Node('bar', [
                Link('link1', Sequence[TypeRef['foo']],
                     _link_func, requires='missing1'),
            ]),
            Root([
                Link('link2', Sequence[TypeRef['foo']],
                     _link_func, requires='missing2'),
            ]),
        ],
        ['Link "link2" requires missing field "missing2" in the "root" node',
         'Link "link1" requires missing field "missing1" in the "bar" node'],
    )


def test_link_contain_invalid_types():
    check_errors(
        [
            Node('foo', []),
            Node('bar', [
                Field('id', None, _fields_func),
                Link('baz', Sequence[TypeRef['foo']],
                     _link_func, requires='id',
                     options=[Option('size', None), 1]),
            ]),
        ],
        [('Invalid types provided as link "bar.baz" options: {!r}'
          .format(int))],
    )
