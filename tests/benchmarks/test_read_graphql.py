from hiku.query import (
    Node,
    Field,
)
from hiku.readers.graphql import (
    read,
    read_rust_real,
    read_rust_and_ast_mock,
    read_ast_mock,
)


QUERY = '{ name }'
EXPECT = Node([Field('name')])


def test_py(benchmark):
    parsed_query = benchmark(read, QUERY, None)
    assert parsed_query == EXPECT


def test_ast_mock(benchmark):
    parsed_query = benchmark(read_ast_mock, QUERY, None)
    assert parsed_query == EXPECT


def test_rust_real(benchmark):
    parsed_query = benchmark(read_rust_real, QUERY, None)
    assert parsed_query == EXPECT


def test_rust_mock(benchmark):
    parsed_query = benchmark(read_rust_and_ast_mock, QUERY, None)
    assert parsed_query == EXPECT
