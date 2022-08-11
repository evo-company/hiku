from hiku.query import (
    Node,
    Field,
)
from hiku.readers.graphql import read


def test_field(benchmark):
    parsed_query = benchmark(read, '{ name }', None)
    assert parsed_query == Node([Field('name')])
