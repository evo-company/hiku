from hiku.executors.sync import SyncExecutor
from hiku.graph import Field, Graph, Link, Node, Root
from hiku.schema import Schema
from hiku.types import Integer, TypeRef


def link_bar(ids):
    import random

    return [random.randrange(1000) for _ in ids]


def map_id(fields, objs):
    return [[obj] * len(fields) for obj in objs]


def map_const(value):
    def mapper(fields, objs):
        return [[value] * len(fields)] * len(objs)

    return mapper


def test_weird_case():
    '''Inconsistent link key, different subsets'''
    graph = Graph(
        [
            Node("Bar", [Field("id", Integer, map_const(1)), Field("id2", Integer, map_const(1))]),
            Node(
                "Foo",
                [
                    Field("id", Integer, map_id),
                    Link("bar", TypeRef["Bar"], link_bar, requires='id')
                ]
            ),
            Root(
                [
                    Link(
                        "foo",
                        TypeRef["Foo"],
                        lambda: 123,
                        requires=None,
                    ),
                ]
            ),
        ],
    )

    query = """
    query Testtest {
      foo1: foo {
        id
        bar {
          id
        }
      }
      foo2: foo {
        id
        bar {
          id2
        }
      }
    }
    """

    schema = Schema(SyncExecutor(), graph)
    schema.execute_sync(query)
    assert False
