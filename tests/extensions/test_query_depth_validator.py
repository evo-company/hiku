import pytest

from hiku.extensions.query_depth_validator import QueryDepthValidator
from hiku.schema import Schema
from hiku.types import Sequence, String, TypeRef
from hiku.executors.sync import SyncExecutor
from hiku.engine import Engine
from hiku.graph import Field, Link, Node, Root, Graph


def noop(*args, **kwargs):
    pass


@pytest.fixture(name="sync_graph")
def sync_graph_fixture():
    return Graph([
        Node('User', [
            Field('id', String, noop),
            Field('name', String, noop),
            Link('friends', Sequence[TypeRef['User']], noop, requires='id'),
        ]),
        Root([
            Link("user", TypeRef['User'], noop, requires=None),
        ])
    ])


def test_query_depth_validator(sync_graph):
    schema = Schema(
        Engine(SyncExecutor()), sync_graph,
        extensions=[
            QueryDepthValidator(max_depth=2),
        ],
    )

    query = """
    query {
        user {
            id
            name
            friends {
                id
                name
                friends {
                    id
                    name
                }
            }
        }
    }
    """

    result = schema.execute_sync({"query": query})
    assert result == {"errors": [{"message": "Query depth 4 exceeds maximum allowed depth 2"}]}
