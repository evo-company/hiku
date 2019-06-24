import pytest

from hiku.compat import PY36, PYPY

if not PY36 or PYPY:  # noqa
    pytest.skip("graphql-core-next library requires Python>=3.6",
                allow_module_level=True)

from hiku.readers.graphql import read
from hiku.endpoint.graphql import _StripQuery


def test_strip():
    query = read("""
    query {
        __typename
        foo {
            __typename
            bar {
                __typename
                baz
            }
        }
    }
    """)
    assert _StripQuery().visit(query) == read("""
    query {
        foo {
            bar {
                baz
            }
        }
    }
    """)
