from hiku.graph import Field, Graph, Link, Node, Root
from hiku.types import String, TypeRef
from hiku.schema import Schema
from hiku.executors.sync import SyncExecutor


def mock_resolve():
    ...


GRAPH = Graph(
    [
        Node(
            "User",
            [
                Field("id", String, mock_resolve),
            ],
        ),
        Root(
            [Link("user", TypeRef["User"], mock_resolve, requires=None)]
        ),
    ],
)


def test_schema__non_existing_link():
    src = """
    query TestQuery {
        nonExistingLink { id }
    }
    """
    schema = Schema(SyncExecutor(), GRAPH)
    result = schema.execute_sync(src)
    assert result.errors is not None
    assert len(result.errors) == 1
    assert result.errors[0].message == 'Link "nonExistingLink" is not implemented in the "root" node'
