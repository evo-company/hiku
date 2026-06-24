import pytest

from hiku.directives import Deprecated
from hiku.graph import Graph, Input, Node, Field, Root, Link, Option, Union, Interface
from hiku.types import InputRef, Integer, TypeRef, Sequence
from hiku.validate.graph import GraphValidationError
from hiku.scalar import Scalar
from hiku.enum import BaseEnum


def _fields_func(fields, ids):
    pass


def _link_func(ids):
    pass


def check_errors(
    graph_items,
    errors,
    scalars=None,
    unions=None,
    interfaces=None,
    enums=None,
    inputs=None,
):
    with pytest.raises(GraphValidationError) as err:
        Graph(
            graph_items,
            scalars=scalars,
            unions=unions,
            interfaces=interfaces,
            enums=enums,
            inputs=inputs,
        )
    assert err.value.errors == errors


def test_graph_contain_duplicate_nodes():
    check_errors(
        [
            Node("foo", []),
            Node("foo", []),
        ],
        ['Duplicated nodes found in the graph: "foo"'],
    )


def test_graph_contain_invalid_types():
    check_errors(
        [
            1,
            Node("foo", []),
        ],
        [("Graph can not contain these types: {!r}".format(int))],
    )


def test_node_contain_duplicate_fields():
    check_errors(
        [
            Root(
                [
                    Field("b", None, _fields_func),
                ]
            ),
            Node(
                "foo",
                [
                    Field("a", None, _fields_func),
                    Field("a", None, _fields_func),
                ],
            ),
            Root(
                [
                    Field("b", None, _fields_func),
                ]
            ),
        ],
        [
            'Duplicated names found in the "root" node: "b"',
            'Duplicated names found in the "foo" node: "a"',
        ],
    )


def test_node_contain_node():
    check_errors(
        [
            Root(
                [
                    Node("foo", []),
                ]
            ),
            Node(
                "bar",
                [
                    Node("baz", []),
                ],
            ),
        ],
        [
            "Node can not contain these types: "
            "<class 'hiku.graph.Node'> in node \"root\"",
            "Node can not contain these types: "
            "<class 'hiku.graph.Node'> in node \"bar\"",
        ],
    )


def test_node_contain_invalid_types():
    check_errors(
        [
            Node(
                "foo",
                [
                    1,
                    Field("bar", None, _fields_func),
                ],
            ),
        ],
        [('Node can not contain these types: {!r} in node "foo"'.format(int))],
    )


def test_option_default_none_with_non_optional_type():
    check_errors(
        [
            Node(
                "foo",
                [
                    Field("bar", None, _fields_func, options=[
                        Option("bar", Integer, default=None),
                    ]),
                ],
            ),
        ],
        ['Non-optional option "foo.bar:bar" must have a default value'],
    )


def test_option_input_ref_has_default_none_but_type_non_optional():
    with pytest.raises(GraphValidationError) as err:
        Graph(
            [
                Node(
                    "User",
                    [
                        Field("avatar", None, _fields_func, options=[
                            Option("params", InputRef["ImageParams"]),
                        ]),
                    ],
                ),
            ], inputs=[
                Input("ImageParams", [
                    Option("width", Integer, default=None),
                ])
            ]
        )
    assert err.value.errors == ['Non-optional option "ImageParams:width" must have a default value']


def test_deprecated_input_argument_with_required_type_must_have_default_value():
    with pytest.raises(GraphValidationError) as err:
        Graph(
            [
                Node(
                    "User",
                    [
                        Field("avatar", None, _fields_func, options=[
                            Option("params", InputRef["ImageParams"]),
                        ]),
                    ],
                ),
            ], inputs=[
                Input("ImageParams", [
                    Option("width", Integer, deprecated="do not use"),
                ])
            ]
        )

    assert err.value.errors == [
        'Required input field "ImageParams:width" cannot be deprecated. '
        'Add default value or make it optional'
    ]


def test_link_missing_node():
    check_errors(
        [
            Node(
                "bar",
                [
                    Link(
                        "link",
                        Sequence[TypeRef["missing"]],
                        _link_func,
                        requires=None,
                    ),
                ],
            ),
        ],
        ['Link "bar.link" points to the missing node "missing"'],
    )


def test_link_requires_missing_field():
    check_errors(
        [
            Node("foo", []),
            Node(
                "bar",
                [
                    Link(
                        "link1",
                        Sequence[TypeRef["foo"]],
                        _link_func,
                        requires="missing1",
                    ),
                ],
            ),
            Root(
                [
                    Link(
                        "link2",
                        Sequence[TypeRef["foo"]],
                        _link_func,
                        requires="missing2",
                    ),
                ]
            ),
        ],
        [
            'Link "link2" requires missing field "missing2" in the "root" node',
            'Link "link1" requires missing field "missing1" in the "bar" node',
        ],
    )


def test_link_contain_invalid_types():
    check_errors(
        [
            Node("foo", []),
            Node(
                "bar",
                [
                    Field("id", None, _fields_func),
                    Link(
                        "baz",
                        Sequence[TypeRef["foo"]],
                        _link_func,
                        requires="id",
                        options=[Option("size", None), 1],
                    ),
                ],
            ),
        ],
        [
            (
                'Invalid types provided as link "bar.baz" options: {!r}'.format(
                    int
                )
            )
        ],
    )


def test_node_uses_deprecated_directive():
    check_errors(
        [
            Node(
                "bar",
                [
                    Field("id", None, _fields_func),
                ],
                directives=[Deprecated("do not use")],
            ),
        ],
        ["Deprecated directive can not be used in Node"],
    )


def test_field_uses_more_than_one_deprecated_directive():
    check_errors(
        [
            Node(
                "bar",
                [
                    Field(
                        "id",
                        None,
                        _fields_func,
                        directives=[
                            Deprecated("do not use"),
                            Deprecated("do not use 2"),
                        ],
                    ),
                ],
            ),
        ],
        ['Deprecated directive must be used only once for "bar.id", found 2'],
    )

def test_deprecated_directive_with_deprecated_argument():
    check_errors(
        [
            Node(
                "bar",
                [
                    Field(
                        "id",
                        None,
                        _fields_func,
                        directives=[
                            Deprecated("do not use"),
                        ],
                        deprecated="do not use 2",
                    ),
                ],
            ),
        ],
        ['Deprecated directive must be used only once for "bar.id", found 2'],
    )


def test_link_uses_more_than_one_deprecated_directive():
    check_errors(
        [
            Node("foo", []),
            Node(
                "bar",
                [
                    Link(
                        "baz",
                        Sequence[TypeRef["foo"]],
                        _link_func,
                        requires=None,
                        directives=[
                            Deprecated("do not use"),
                            Deprecated("do not use 2"),
                        ],
                    )
                ],
            ),
        ],
        ['Deprecated directive must be used only once for "bar.baz", found 2'],
    )


def test_graph_contain_duplicate_nodes():
    check_errors(
        [
            Node("foo", [], description=tuple("foo")),
        ],
        ['Node "foo" description must be a string'],
    )


def test_scalar_and_node_same_name():
    class CoolType(Scalar):
        pass

    check_errors(
        [
            Node("CoolType", []),
        ],
        [
            'Scalar "CoolType" has the same name as node "CoolType". '
            "GraphQL schema cannot have a scalar and a type with the same name."
        ],
        scalars=[CoolType],
    )


def test_scalar_and_union_same_name():
    class CoolType(Scalar):
        pass

    check_errors(
        [
            Node("User", []),
        ],
        [
            'Scalar "CoolType" has the same name as union "CoolType". '
            "GraphQL schema cannot have a scalar and a type with the same name."
        ],
        scalars=[CoolType],
        unions=[Union("CoolType", ["User"])],
    )


def test_scalar_and_interface_same_name():
    class CoolType(Scalar):
        pass

    check_errors(
        [
            Node("User", []),
        ],
        [
            'Scalar "CoolType" has the same name as interface "CoolType". '
            "GraphQL schema cannot have a scalar and a type with the same name."
        ],
        scalars=[CoolType],
        interfaces=[Interface("CoolType", [])],
    )


def test_scalar_and_enum_same_name():
    class CoolType(Scalar):
        pass

    class CoolTypeEnum(BaseEnum):
        name = "CoolType"
        values = ["VALUE1", "VALUE2"]

    check_errors(
        [
            Node("User", []),
        ],
        [
            'Scalar "CoolType" has the same name as enum "CoolType". '
            "GraphQL schema cannot have a scalar and a type with the same name."
        ],
        scalars=[CoolType],
        enums=[CoolTypeEnum],
    )


def test_scalar_and_input_same_name():
    class CoolType(Scalar):
        pass

    check_errors(
        [
            Node("User", []),
        ],
        [
            'Scalar "CoolType" has the same name as input "CoolType". '
            "GraphQL schema cannot have a scalar and a type with the same name."
        ],
        scalars=[CoolType],
        inputs=[Input("CoolType", [])],
    )


def test_multiple_scalar_collisions():
    class CoolType(Scalar):
        pass

    class AnotherType(Scalar):
        pass

    check_errors(
        [
            Node("CoolType", []),
            Node("AnotherType", []),
        ],
        [
            'Scalar "AnotherType" has the same name as node "AnotherType". '
            "GraphQL schema cannot have a scalar and a type with the same name.",
            'Scalar "CoolType" has the same name as node "CoolType". '
            "GraphQL schema cannot have a scalar and a type with the same name.",
        ],
        scalars=[CoolType, AnotherType],
    )