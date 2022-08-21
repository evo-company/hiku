import pytest

from hiku.query import (
    Node,
    Field,
)
from hiku.readers.graphql import (
    read,
    read_rust,
)


SMALL = 5
MEDIUM = 25
LARGE = 500

FIELD_NAME = 'somesuperlongfieldname'


def gen_fields(size):
    for idx in range(size):
        yield f'{FIELD_NAME}_{idx}'


def gen_query(size):
    return '{' + ' '.join(list(gen_fields(size))) + '}'


def gen_node(size):
    return Node([
        Field(field) for field in gen_fields(size)
    ])


QUERY_SMALL = gen_query(SMALL)
QUERY_MEDIUM = gen_query(MEDIUM)
QUERY_LARGE = gen_query(LARGE)

RESULT_SMALL = gen_node(SMALL)
RESULT_MEDIUM = gen_node(MEDIUM)
RESULT_LARGE = gen_node(LARGE)


@pytest.mark.benchmark(group='small')
def test_py_small(benchmark):
    parsed_query = benchmark(read, QUERY_SMALL, None)
    assert parsed_query == RESULT_SMALL


@pytest.mark.benchmark(group='small')
def test_rust_small(benchmark):
    parsed_query = benchmark(read_rust, QUERY_SMALL, None)
    assert parsed_query == RESULT_SMALL


@pytest.mark.benchmark(group='medium')
def test_py_medium(benchmark):
    parsed_query = benchmark(read, QUERY_MEDIUM, None)
    assert parsed_query == RESULT_MEDIUM


@pytest.mark.benchmark(group='medium')
def test_rust_medium(benchmark):
    parsed_query = benchmark(read_rust, QUERY_MEDIUM, None)
    assert parsed_query == RESULT_MEDIUM


@pytest.mark.benchmark(group='large')
def test_py_large(benchmark):
    parsed_query = benchmark(read, QUERY_LARGE, None)
    assert parsed_query == RESULT_LARGE


@pytest.mark.benchmark(group='large')
def test_rust_large(benchmark):
    parsed_query = benchmark(read_rust, QUERY_LARGE, None)
    assert parsed_query == RESULT_LARGE
