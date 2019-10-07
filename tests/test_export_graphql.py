import pytest

from hiku.compat import PY36, PYPY

if not PY36 or PYPY:  # noqa
    pytest.skip("graphql-core-next library requires Python>=3.6",
                allow_module_level=True)

from graphql.language.printer import print_ast

from hiku.query import Field, Link, Node
from hiku.export.graphql import export


def check_export(query_obj, data):
    assert print_ast(export(query_obj)) == data


def test_field():
    check_export(Node([Field('foo')]), '{\n  foo\n}\n')


def test_link():
    check_export(
        Node([Link('foo', Node([Field('bar')]))]),
        '{\n  foo {\n    bar\n  }\n}\n',
    )


def test_options():
    check_export(
        Node([Field('foo', options={'bar': [1, {'baz': 2}, 3]})]),
        '{\n  foo(bar: [1, {baz: 2}, 3])\n}\n',
    )
