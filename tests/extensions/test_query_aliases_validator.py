import pytest

from hiku.executors.sync import SyncExecutor
from hiku.extensions.query_aliases_validator import QueryAliasesValidator
from hiku.schema import Schema
from hiku.types import Sequence, String, TypeRef
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


def test_query_aliases_validator_rejects_too_many_aliases(sync_graph):
    schema = Schema(
        SyncExecutor(), sync_graph,
        extensions=[
            QueryAliasesValidator(max_aliases=2),
        ],
    )

    query = """
    query {
        user {
            a: id
            b: name
            c: id
        }
    }
    """

    result = schema.execute_sync(query)
    assert [e.message for e in result.errors] == [
        "Query uses 3 aliases which exceeds maximum "
        "allowed number of aliases 2"
    ]


def test_query_aliases_validator_counts_link_aliases(sync_graph):
    schema = Schema(
        SyncExecutor(), sync_graph,
        extensions=[
            QueryAliasesValidator(max_aliases=1),
        ],
    )

    query = """
    query {
        first: user {
            id
        }
        second: user {
            id
        }
    }
    """

    result = schema.execute_sync(query)
    assert [e.message for e in result.errors] == [
        "Query uses 2 aliases which exceeds maximum "
        "allowed number of aliases 1"
    ]


def test_query_aliases_validator_allows_within_limit():
    def user_fields(fields, ids):
        return [
            [{"id": "1", "name": "John"}[f.name] for f in fields]
            for _ in ids
        ]

    def to_user():
        return 1

    graph = Graph([
        Node('User', [
            Field('id', String, user_fields),
            Field('name', String, user_fields),
        ]),
        Root([
            Link("user", TypeRef['User'], to_user, requires=None),
        ])
    ])

    schema = Schema(
        SyncExecutor(), graph,
        extensions=[
            QueryAliasesValidator(max_aliases=3),
        ],
    )

    query = """
    query {
        user {
            a: id
            b: name
        }
    }
    """

    result = schema.execute_sync(query)
    assert result.errors is None
    assert result.data == {"user": {"a": "1", "b": "John"}}
