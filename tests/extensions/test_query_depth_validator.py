import pytest

from hiku.executors.sync import SyncExecutor
from hiku.extensions.query_depth_validator import QueryDepthValidator
from hiku.schema import Schema
from hiku.types import Sequence, String, TypeRef
from hiku.graph import Field, Link, Node, Root, Graph


def user_fields(fields, ids):
    return [
        [{"id": str(i), "name": "John"}[f.name] for f in fields]
        for i in ids
    ]


def to_user():
    return 1


def to_friends(ids):
    return [[2] for _ in ids]


@pytest.fixture(name="sync_graph")
def sync_graph_fixture():
    return Graph([
        Node('User', [
            Field('id', String, user_fields),
            Field('name', String, user_fields),
            Link(
                'friends', Sequence[TypeRef['User']], to_friends,
                requires='id',
            ),
        ]),
        Root([
            Link("user", TypeRef['User'], to_user, requires=None),
        ])
    ])


def test_query_depth_validator(sync_graph):
    schema = Schema(
        SyncExecutor(), sync_graph,
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

    result = schema.execute_sync(query)
    assert [e.message for e in result.errors] == ["Query depth 4 exceeds maximum allowed depth 2"]


def test_query_depth_within_limit_with_fragments(sync_graph):
    schema = Schema(
        SyncExecutor(), sync_graph,
        extensions=[
            QueryDepthValidator(max_depth=2),
        ],
    )

    query = """
    query {
        user {
            id
            ... on User {
                name
            }
        }
    }
    """

    # Fragment fields stay in the user selection set, so depth is 2.
    result = schema.execute_sync(query)
    assert result.errors is None
    assert result.data == {"user": {"id": "1", "name": "John"}}


def test_query_depth_validator_with_fragments(sync_graph):
    schema = Schema(
        SyncExecutor(), sync_graph,
        extensions=[
            QueryDepthValidator(max_depth=2),
        ],
    )

    query = """
    query {
        user {
            id
            name
            ... on User {
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
    }
    """

    result = schema.execute_sync(query)
    assert [e.message for e in result.errors] == ["Query depth 4 exceeds maximum allowed depth 2"]
