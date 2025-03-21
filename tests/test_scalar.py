from datetime import datetime

import pytest

from hiku.executors.sync import SyncExecutor
from hiku.graph import Field, Graph, Link, Node, Nothing, Option, Root
from hiku.scalar import DateTime, Scalar
from hiku.schema import Schema
from hiku.types import Float, Integer, Optional, Sequence, TypeRef
from hiku.utils import listify
from hiku.readers.graphql import read
from hiku.validate.graph import GraphValidationError
from hiku.validate.query import validate


def execute(graph, query):
    schema = Schema(SyncExecutor(), graph)
    return schema.execute_sync(query)


class SomeType:
    ...


def test_validate_graph_invalid_scalars():
    with pytest.raises(GraphValidationError) as err:
        Graph(
            [
                Node(
                    "User",
                    [
                        Field("id", Integer, lambda: None),
                        Field("dateCreated", SomeType, lambda: None),
                    ],
                ),
                Root(
                    [
                        Link(
                            "user",
                            Optional[TypeRef["User"]],
                            lambda: None,
                            requires=None,
                        ),
                    ]
                ),
            ]
        )

    assert err.value.errors == [
        'Field "User.dateCreated" has type "<class \'tests.test_scalar.SomeType\'>" but Hiku does not support it.',
    ]


def test_validate_graph_not_defined_scalars():
    class SomeType(Scalar):
        ...

    with pytest.raises(GraphValidationError) as err:
        Graph(
            [
                Node(
                    "User",
                    [
                        Field("id", Integer, lambda: None),
                        Field("dateCreated", SomeType, lambda: None),
                    ],
                ),
                Root(
                    [
                        Link(
                            "user",
                            Optional[TypeRef["User"]],
                            lambda: None,
                            requires=None,
                        ),
                    ]
                ),
            ]
        )

    assert err.value.errors == [
        'Field "User.dateCreated" has type "<class \'tests.test_scalar.test_validate_graph_not_defined_scalars.<locals>.SomeType\'>" but no scalar is defined for it. '
        "Maybe you forgot to add new scalar to Graph(..., scalars)?",
    ]


DATE_CREATED = datetime(2023, 6, 15, 12, 30, 59, 0)
DATE_CREATED_STR = "2023-06-15T12:30:59"  # TODO: check timezone


def test_serialize_scalar_field_correct():
    @listify
    def resolve_user_fields(fields, ids):
        def get_field(fname, id_):
            if fname == "id":
                return id_
            elif fname == "dateCreated":
                return DATE_CREATED
            elif fname == "dateCreatedMany":
                return [DATE_CREATED]
            elif fname == "dateCreatedManyOptional":
                return [DATE_CREATED, None]
            elif fname == "dateCreatedMaybe":
                return None
            elif fname == "dateCreatedMaybeSequence":
                return []

        for id_ in ids:
            yield [get_field(f.name, id_) for f in fields]

    graph = Graph(
        [
            Node(
                "User",
                [
                    Field("id", Integer, resolve_user_fields),
                    Field("dateCreated", DateTime, resolve_user_fields),
                    Field(
                        "dateCreatedMany",
                        Sequence[DateTime],
                        resolve_user_fields,
                    ),
                    Field(
                        "dateCreatedManyOptional",
                        Sequence[Optional[DateTime]],
                        resolve_user_fields,
                    ),
                    Field(
                        "dateCreatedMaybe",
                        Optional[DateTime],
                        resolve_user_fields,
                    ),
                    Field(
                        "dateCreatedMaybeSequence",
                        Optional[Sequence[DateTime]],
                        resolve_user_fields,
                    ),
                ],
            ),
            Root(
                [
                    Link(
                        "user",
                        Optional[TypeRef["User"]],
                        lambda: 1,
                        requires=None,
                    ),
                ]
            ),
        ],
        scalars=[DateTime],
    )

    query = """
    query GetUser {
      user {
        id
        dateCreated
        dateCreatedMany
        dateCreatedManyOptional
        dateCreatedMaybe
        dateCreatedMaybeSequence
      }
    }
    """
    result = execute(graph, read(query))
    assert result.data == {
        "user": {
            "id": 1,
            "dateCreated": DATE_CREATED_STR,
            "dateCreatedMany": [DATE_CREATED_STR],
            "dateCreatedManyOptional": [DATE_CREATED_STR, None],
            "dateCreatedMaybe": None,
            "dateCreatedMaybeSequence": [],
        }
    }


def test_parse_scalar_input_correct():
    @listify
    def resolve_user_fields(fields, ids):
        def get_field(fname, id_):
            if fname == "id":
                return id_
            elif fname == "dateCreated":
                return DATE_CREATED

        for id_ in ids:
            yield [get_field(f.name, id_) for f in fields]

    def link_user(opts):
        if opts["dateCreated"] == DATE_CREATED:
            return 1

        return Nothing

    graph = Graph(
        [
            Node(
                "User",
                [
                    Field("id", Integer, resolve_user_fields),
                    Field("dateCreated", DateTime, resolve_user_fields),
                ],
            ),
            Root(
                [
                    Link(
                        "user",
                        Optional[TypeRef["User"]],
                        link_user,
                        requires=None,
                        options=[
                            Option("dateCreated", DateTime),
                            Option("dateCreatedMany", Sequence[DateTime]),
                            Option("dateCreatedMaybe", Optional[DateTime]),
                        ],
                    ),
                ]
            ),
        ],
        scalars=[DateTime],
    )

    query = """
    query GetUser {
      user(dateCreated: "%s", dateCreatedMany: ["%s"], dateCreatedMaybe: null) {
        id
        dateCreated
      }
    }
    """ % (
        DATE_CREATED_STR,
        DATE_CREATED_STR,
    )

    result = execute(graph, read(query))
    assert result.data == {
        "user": {
            "id": 1,
            "dateCreated": DATE_CREATED_STR,
        }
    }


def test_validate_scalar_input_correct():
    graph = Graph(
        [
            Node(
                "User",
                [
                    Field("id", Integer, lambda fields, ids: None),
                    Field("dateCreated", DateTime, lambda fields, ids: None),
                ],
            ),
            Root(
                [
                    Link(
                        "user",
                        Optional[TypeRef["User"]],
                        lambda opts: None,
                        requires=None,
                        options=[
                            Option("dateCreated", DateTime),
                            Option("dateCreatedMany", Sequence[DateTime]),
                            Option("dateCreatedMaybe", Optional[DateTime]),
                        ],
                    ),
                ]
            ),
        ],
        scalars=[DateTime],
    )

    query = """
    query GetUser {
      user(dateCreated: "%s", dateCreatedMany: ["%s"], dateCreatedMaybe: null) {
        id
        dateCreated
      }
    }
    """ % (
        DATE_CREATED_STR,
        DATE_CREATED_STR,
    )

    errors = validate(graph, read(query))
    assert errors == []


INT_VALUE = 60


def test_parse_float_input_correct():
    @listify
    def resolve_user_fields(fields, ids):
        def get_field(fname, id_):
            if fname == "id":
                return id_
            if fname == "weight":
                return INT_VALUE

        for id_ in ids:
            yield [get_field(f.name, id_) for f in fields]

    def link_user(opts):
        assert type(opts["weight"]) == float, "Must be converted to float"
        if opts["weight"] == INT_VALUE:
            return 1

        return Nothing

    graph = Graph(
        [
            Node(
                "User",
                [
                    Field("id", Integer, resolve_user_fields),
                    Field("weight", Float, resolve_user_fields),
                ],
            ),
            Root(
                [
                    Link(
                        "user",
                        Optional[TypeRef["User"]],
                        link_user,
                        requires=None,
                        options=[
                            Option("weight", Float),
                        ],
                    ),
                ]
            ),
        ],
    )

    query = """
    query GetUser {
      user(weight: %s) {
        id
        weight
      }
    }
    """ % (
        INT_VALUE,
    )

    result = execute(graph, read(query))
    assert result.data == {
        "user": {
            "id": 1,
            "weight": INT_VALUE,
        }
    }


def test_validate_float_input_correct():
    graph = Graph(
        [
            Node(
                "User",
                [
                    Field("id", Integer, lambda fields, ids: None),
                    Field("weight", Float, lambda fields, ids: None),
                ],
            ),
            Root(
                [
                    Link(
                        "user",
                        Optional[TypeRef["User"]],
                        lambda opts: None,
                        requires=None,
                        options=[
                            Option("weight", Float),
                        ],
                    ),
                ]
            ),
        ],
    )

    query = """
    query GetUser {
      user(weight: %s) {
        id
        weight
      }
    }
    """ % (
        INT_VALUE,
    )

    errors = validate(graph, read(query))
    assert errors == []


def test_parse_float_input_incorrect():
    @listify
    def resolve_user_fields(fields, ids):
        def get_field(fname, id_):
            if fname == "id":
                return id_
            if fname == "weight":
                return INT_VALUE

        for id_ in ids:
            yield [get_field(f.name, id_) for f in fields]

    def link_user(opts):
        # assert type(opts["weight"]) == float, "Must be converted to float"
        if opts["weight"] == INT_VALUE:
            return 1

        return Nothing

    graph = Graph(
        [
            Node(
                "User",
                [
                    Field("id", Integer, resolve_user_fields),
                    Field("weight", Float, resolve_user_fields),
                ],
            ),
            Root(
                [
                    Link(
                        "user",
                        Optional[TypeRef["User"]],
                        link_user,
                        requires=None,
                        options=[
                            Option("weight", Float),
                        ],
                    ),
                ]
            ),
        ],
    )

    query = """
    query GetUser {
      user(weight: "%s") {
        id
        weight
      }
    }
    """ % (
        INT_VALUE,
    )

    result = execute(graph, read(query))
    assert result.data == None
    assert len(result.errors) == 1
    assert (
        result.errors[0].message
        == 'Invalid value for option "root.user:weight", "str" instead of Float'
    )


def test_validate_float_input_incorrect():
    graph = Graph(
        [
            Node(
                "User",
                [
                    Field("id", Integer, lambda fields, ids: None),
                    Field("weight", Float, lambda fields, ids: None),
                ],
            ),
            Root(
                [
                    Link(
                        "user",
                        Optional[TypeRef["User"]],
                        lambda opts: None,
                        requires=None,
                        options=[
                            Option("weight", Float),
                        ],
                    ),
                ]
            ),
        ],
    )

    query = """
    query GetUser {
      user(weight: "%s") {
        id
        weight
      }
    }
    """ % (
        INT_VALUE,
    )

    errors = validate(graph, read(query))
    assert errors == [
        'Invalid value for option "root.user:weight", "str" instead of Float'
    ]
