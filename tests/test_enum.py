from enum import Enum

import pytest

from hiku.enum import enum

from hiku.denormalize.graphql import DenormalizeGraphQL
from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.graph import Field, Graph, Link, Node, Option, Root
from hiku.types import Integer, Optional, Sequence, TypeRef, EnumRef
from hiku.utils import listify
from hiku.readers.graphql import read
from hiku.validate.graph import GraphValidationError


def execute(graph, query):
    engine = Engine(SyncExecutor())
    result = engine.execute(graph, query, {})
    return DenormalizeGraphQL(graph, result, "query").process(query)


# TODO: DESCRIBE IN DOCS THAT NAME OF ENUM IS WHAT USED IN GRAPH, not value

@enum(name='UserStatus')
class Status(Enum):
    ACTIVE = 'ACTIVE'
    DELETED = 'DELETED'


def test_validate_graph_enums():
    with pytest.raises(GraphValidationError) as err:
        @enum
        class NoValues(Enum):
            ...

        class NoDecorator(Enum):
            ...

        Graph([
            Node('User', [
                Field('id', Integer, lambda: None),
            ]),
            Root([
                Link('user', Optional[TypeRef['User']], lambda: None, requires=None),
            ]),
        ], enums=[
            NoValues,
            NoDecorator
        ])

    assert err.value.errors == [
        'Enum must have at least one value',
        'Enum must be wrapped with @enum decorator'
    ]


def test_serialize_enum_field_correct():
    @listify
    def resolve_user_fields(fields, ids):
        def get_field(fname, id_):
            if fname == 'id':
                return id_
            elif fname == 'status':
                # TODO: we must return enum here, not string, describe in docs
                return Status.ACTIVE
            elif fname == 'statuses':
                return [Status.ACTIVE]
            elif fname == 'maybe_status':
                return None

        for id_ in ids:
            yield [get_field(f.name, id_) for f in fields]

    def link_user():
        return 1

    graph = Graph([
        Node('User', [
            Field('id', Integer, resolve_user_fields),
            Field('status', EnumRef['UserStatus'], resolve_user_fields),
            Field('statuses', Sequence[EnumRef['UserStatus']], resolve_user_fields),
            Field('maybe_status', Optional[EnumRef['UserStatus']], resolve_user_fields),
        ]),
        Root([
            Link('user', Optional[TypeRef['User']], link_user, requires=None),
        ]),
    ], enums=[Status])

    query = """
    query GetUser {
      user {
        id
        status
        statuses
        maybe_status
      }
    }
    """
    result = execute(graph, read(query))
    assert result == {
        'user': {
            'id': 1,
            'status': 'ACTIVE',
            'statuses': ['ACTIVE'],
            'maybe_status': None,
        }
    }


@pytest.mark.parametrize("query", [
    """
    query GetUser { user { id status } } 
    """,
    """
    query GetUser { user { id statuses } } 
    """,
    """
    query GetUser { user { id maybe_status } } 
    """
])
def test_serialize_enum_field_incorrect(query):
    @listify
    def resolve_user_fields(fields, ids):
        def get_field(fname, id_):
            if fname == 'id':
                return id_
            elif fname == 'status':
                return 'ACTIVE'
            elif fname == 'statuses':
                return ['ACTIVE']
            elif fname == 'maybe_status':
                return 'ACTIVE'

        for id_ in ids:
            yield [get_field(f.name, id_) for f in fields]

    def link_user():
        return 1

    graph = Graph([
        Node('User', [
            Field('id', Integer, resolve_user_fields),
            Field('status', EnumRef['UserStatus'], resolve_user_fields),
            Field('statuses', Sequence[EnumRef['UserStatus']], resolve_user_fields),
            Field('maybe_status', Optional[EnumRef['UserStatus']], resolve_user_fields),
        ]),
        Root([
            Link('user', Optional[TypeRef['User']], link_user, requires=None),
        ]),
    ], enums=[Status])

    with pytest.raises(TypeError) as err:
        execute(graph, read(query))

    err.match(
        "Enum 'UserStatus' can not represent value: 'ACTIVE'"
    )


@pytest.mark.parametrize("query, expected", [
    ("query GetUser { user(status: DELETED) { id status } }", (2, 'DELETED')),
    ("query GetUser { user { id status } }", (1, 'ACTIVE')),
])
def test_parse_enum_argument(query, expected):
    def link_user(opt):
        if opt['status'] is Status.ACTIVE:
            return 1
        elif opt['status'] is Status.DELETED:
            return 2
        raise ValueError(
            'Unknown status: {}'.format(opt['status'])
        )

    @listify
    def resolve_user_fields(fields, ids):
        def get_field(fname, id_):
            if fname == 'id':
                return id_
            elif fname == 'status':
                if id_ == 1:
                    return Status.ACTIVE
                return Status.DELETED

        for id_ in ids:
            yield [get_field(f.name, id_) for f in fields]

    graph = Graph([
        Node('User', [
            Field('id', Integer, resolve_user_fields),
            Field('status', EnumRef['UserStatus'], resolve_user_fields),
        ]),
        Root([
            Link(
                'user',
                Optional[TypeRef['User']],
                link_user,
                requires=None,
                options=[
                    Option('status', EnumRef['UserStatus'], default=Status.ACTIVE)
                ]
            ),
        ]),
    ], enums=[Status])

    result = execute(graph, read(query))
    assert result == {
        'user': {
            'id': expected[0],
            'status': expected[1],
        }
    }


def test_parse_enum_invalid_argument():
    graph = Graph([
        Node('User', [
            Field('id', Integer, lambda: None),
        ]),
        Root([
            Link(
                'user',
                Optional[TypeRef['User']],
                lambda: None,
                requires=None,
                options=[
                    Option('status', EnumRef['UserStatus'])
                ]
            ),
        ]),
    ], enums=[Status])

    query = """
        query GetUser { user(status: INVALID) { id } }
    """
    with pytest.raises(TypeError) as err:
        execute(graph, read(query))

    err.match("Value 'INVALID' does not exist in 'UserStatus' enum")
