from hiku.query import (
    Node,
    Field,
    Link,
)
from hiku.readers.graphql import (
    read,
    read_rust_apollo,
    read_rust_graphql_parser,
)


def test_read_query_py(benchmark):
    parsed_query = benchmark(read, 'query User { user(id: 1) { name } }', None)
    # assert parsed_query == Node([
    #     Link('user', Node([
    #         Field('name')
    #     ]), options={'id': 1})
    # ])


def test_read_query_rust_apollo(benchmark):
    parsed_query = benchmark(read_rust_apollo, 'query User { user(id: 1) { name } }', None)
    assert parsed_query.kind == "node"
    # assert parsed_query == Node([
    #     Link('user', Node([
    #         Field('name')
    #     ]), options={'id': 1})
    # ])


def test_read_query_rust_graphql_parser(benchmark):
    parsed_query = benchmark(read_rust_graphql_parser, 'query User { user(id: 1) { name } }', None)
    assert parsed_query.kind == "node"

# def test_read_query_rust_debug():
#     parsed_query = read_rust('query User { user(id: 1) { name } }', None)
#     assert parsed_query == Node([
#         Link('user', Node([
#             Field('name')
#         ]), options={'id': 1})
#     ])
