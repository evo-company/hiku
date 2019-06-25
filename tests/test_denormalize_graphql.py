import pytest

from hiku.compat import PY36, PYPY

if not PY36 or PYPY:  # noqa
    pytest.skip("graphql-core-next library requires Python>=3.6",
                allow_module_level=True)

from hiku.types import TypeRef, Integer, Sequence
from hiku.graph import Graph, Node, Field, Root, Link
from hiku.result import ROOT, Proxy, Index, Reference
from hiku.readers.graphql import read
from hiku.denormalize.graphql import DenormalizeGraphQL


def _(*args):
    raise NotImplementedError('Data loading not implemented')


def test_typename():
    graph = Graph([
        Node('Bar', [
            Field('baz', Integer, _),
        ]),
        Node('Foo', [
            Link('bar', Sequence[TypeRef['Bar']], _, requires=None),
        ]),
        Root([
            Link('foo', TypeRef['Foo'], _, requires=None),
        ]),
    ])
    query = read("""
    query {
        __typename
        foo {
            __typename
            bar {
                __typename
                baz
            }
        }
    }
    """)
    index = Index()
    index[ROOT.node][ROOT.ident].update({
        'foo': Reference('Foo', 1),
    })
    index['Foo'][1].update({
        'bar': [Reference('Bar', 2), Reference('Bar', 3)],
    })
    index['Bar'][2].update({
        'baz': 42
    })
    index['Bar'][3].update({
        'baz': 43
    })
    result = Proxy(index, ROOT, query)
    assert DenormalizeGraphQL(graph, result, 'Query').process(query) == {
        '__typename': 'Query',
        'foo': {
            '__typename': 'Foo',
            'bar': [
                {
                    '__typename': 'Bar',
                    'baz': 42,
                },
                {
                    '__typename': 'Bar',
                    'baz': 43,
                },
            ],
        },
    }
