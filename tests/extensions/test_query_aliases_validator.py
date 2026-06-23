import pytest

from hiku.executors.sync import SyncExecutor
from hiku.extensions.query_aliases_validator import QueryAliasesValidator
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


def test_rejects_too_many_aliases_to_same_field(sync_graph):
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
            b: id
            c: id
        }
    }
    """

    result = schema.execute_sync(query)
    assert [e.message for e in result.errors] == [
        "Field 'id' is aliased more than 2 times"
    ]


def test_aliases_to_different_fields_counted_separately(sync_graph):
    schema = Schema(
        SyncExecutor(), sync_graph,
        extensions=[
            QueryAliasesValidator(max_aliases=1),
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


def test_aliases_counted_per_selection_set(sync_graph):
    schema = Schema(
        SyncExecutor(), sync_graph,
        extensions=[
            QueryAliasesValidator(max_aliases=1),
        ],
    )

    query = """
    query {
        user {
            a: id
            friends {
                b: id
                c: id
            }
        }
    }
    """

    # 'id' is aliased once at user level (ok) and twice under friends (exceeds).
    result = schema.execute_sync(query)
    assert [e.message for e in result.errors] == [
        "Field 'id' is aliased more than 1 times"
    ]


def test_link_aliases_to_same_link_counted(sync_graph):
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
        "Field 'user' is aliased more than 1 times"
    ]


def test_aliases_in_fragments_merge_into_parent_selection_set(sync_graph):
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
            b: id
            ... on User {
                c: id
            }
        }
    }
    """

    result = schema.execute_sync(query)
    assert [e.message for e in result.errors] == [
        "Field 'id' is aliased more than 2 times"
    ]


def test_aliases_within_limit_with_fragments(sync_graph):
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
            ... on User {
                b: id
            }
        }
    }
    """

    result = schema.execute_sync(query)
    assert result.errors is None
    assert result.data == {"user": {"a": "1", "b": "1"}}


def test_same_alias_across_fragments_counted_once(sync_graph):
    schema = Schema(
        SyncExecutor(), sync_graph,
        extensions=[
            QueryAliasesValidator(max_aliases=1),
        ],
    )

    query = """
    query {
        user {
            a: id
            ... on User {
                a: id
            }
        }
    }
    """

    # The duplicated 'a' alias merges into a single field, so only one distinct
    # alias to 'id' exists and the limit is not exceeded.
    result = schema.execute_sync(query)
    assert result.errors is None
    assert result.data == {"user": {"a": "1"}}


def test_aliases_counted_per_selection_set_within_limit(sync_graph):
    schema = Schema(
        SyncExecutor(), sync_graph,
        extensions=[
            QueryAliasesValidator(max_aliases=1),
        ],
    )

    query = """
    query {
        user {
            a: id
            friends {
                b: id
            }
        }
    }
    """

    result = schema.execute_sync(query)
    assert result.errors is None
    assert result.data == {"user": {"a": "1", "friends": [{"b": "2"}]}}
