from graphql.language.printer import print_ast

from hiku.query import Field, Fragment, Link, Node
from hiku.export.graphql import export


def check_export(query_obj, data):
    assert print_ast(export(query_obj)) == data


def test_field():
    check_export(Node([Field("foo")]), "{\n  foo\n}")


def test_link():
    check_export(
        Node([Link("foo", Node([Field("bar")]))]),
        "{\n  foo {\n    bar\n  }\n}",
    )


def test_options():
    check_export(
        Node([Field("foo", options={"bar": [1, {"baz": 2}, 3]})]),
        "{\n  foo(bar: [1, {baz: 2}, 3])\n}",
    )


def test_named_fragments():
    check_export(
        Node(
            [],
            [
                Fragment(
                    "Foo",
                    "Bar",
                    Node(
                        [Field("id")],
                        [Fragment("Baz", "Qux", Node([Field("name")]))],
                    ),
                ),
            ],
        ),
        (
            "{\n"
            "  ...Foo\n"
            "}\n\n"
            "fragment Foo on Bar {\n"
            "  id\n"
            "  ...Baz\n"
            "}\n\n"
            "fragment Baz on Qux {\n"
            "  name\n"
            "}"
        ),
    )
