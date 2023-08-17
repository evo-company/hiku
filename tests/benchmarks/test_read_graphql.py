from hiku.query import (
    Fragment, Link, Node,
    Field,
)
from hiku.readers.graphql import read


def test_field(benchmark):
    parsed_query = benchmark(read, "{ name }", None)
    assert parsed_query == Node([Field("name")])


def test_link(benchmark):
    query = """
    {
        user {
            id
            name
        }
    }

    """
    parsed_query = benchmark(read, query, None)
    assert parsed_query == Node([
        Link("user", Node(
            [
                Field("id"),
                Field("name"),
            ],
            []
        ))
    ])


def test_link_fragment(benchmark):
    query = """
    {
        user {
            id
            ... on User {
                name
            }
        }
    }
    
    """
    parsed_query = benchmark(read, query, None)
    assert parsed_query == Node([
        Link("user", Node(
            [
                Field("id"),
            ],
            [
                Fragment("User", [
                    Field("name"),
                ])
            ]
        ))
    ])
