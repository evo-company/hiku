from enum import Enum as PyEnum

import pytest

from hiku.enum import Enum
from hiku.executors.sync import SyncExecutor
from hiku.graph import Field, Graph, Link, Node, Option, Root
from hiku.schema import Schema
from hiku.types import Integer, Optional, Sequence, TypeRef, EnumRef
from hiku.utils import listify
from hiku.readers.graphql import read
from hiku.validate.graph import GraphValidationError
from hiku.validate.query import validate


def execute(graph, query):
    schema = Schema(SyncExecutor(), graph)
    return schema.execute_sync(query)


class Status(PyEnum):
    ACTIVE = 'ACTIVE'
    DELETED = 'DELETED'


def test_validate_graph_enums():
    with pytest.raises(GraphValidationError) as err:
        Graph([
            Node('User', [
                Field('id', Integer, lambda: None),
            ]),
            Root([
                Link('user', Optional[TypeRef['User']], lambda: None, requires=None),
            ]),
        ], enums=[
            Enum('', ['ACTIVE', 'DELETED']),
            Enum('Status', []),
        ])

    assert err.value.errors == [
        'Enum must have a name',
        'Enum must have at least one value',
    ]


@pytest.mark.parametrize("enum,status", [
    (Enum.from_builtin(Status, 'UserStatus'), Status.ACTIVE),
    (Enum('UserStatus', ['ACTIVE', 'DELETED']), 'ACTIVE'),
])
def test_serialize_enum_field_correct(enum, status):
    @listify
    def resolve_user_fields(fields, ids):
        def get_field(fname, id_):
            if fname == 'id':
                return id_
            elif fname == 'status':
                return status
            elif fname == 'statuses':
                return [status]
            elif fname == 'maybe_status':
                return None

        for id_ in ids:
            yield [get_field(f.name, id_) for f in fields]

    graph = Graph([
        Node('User', [
            Field('id', Integer, resolve_user_fields),
            Field('status', EnumRef['UserStatus'], resolve_user_fields),
            Field('statuses', Sequence[EnumRef['UserStatus']], resolve_user_fields),
            Field('maybe_status', Optional[EnumRef['UserStatus']], resolve_user_fields),
        ]),
        Root([
            Link('user', Optional[TypeRef['User']], lambda: 1, requires=None),
        ]),
    ], enums=[enum])

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
    assert result.data == {
        'user': {
            'id': 1,
            'status': 'ACTIVE',
            'statuses': ['ACTIVE'],
            'maybe_status': None,
        }
    }


@pytest.mark.parametrize("enum,status,field", [
    (Enum.from_builtin(Status, 'UserStatus'), 'ACTIVE', "status"),
    (Enum.from_builtin(Status, 'UserStatus'), 'ACTIVE', "statuses"),
    (Enum.from_builtin(Status, 'UserStatus'), 'ACTIVE', "maybe_status"),
    (Enum('UserStatus', ['ACTIVE', 'DELETED']), Status.ACTIVE, "status"),
    (Enum('UserStatus', ['ACTIVE', 'DELETED']), Status.ACTIVE, "statuses"),
    (Enum('UserStatus', ['ACTIVE', 'DELETED']), Status.ACTIVE, "maybe_status"),
])
def test_serialize_enum_field_incorrect(enum, status, field):
    @listify
    def resolve_user_fields(fields, ids):
        def get_field(fname, id_):
            if fname == 'id':
                return id_
            elif fname == 'status':
                return status
            elif fname == 'statuses':
                return [status]
            elif fname == 'maybe_status':
                return status

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
    ], enums=[enum])

    query = """
    query GetUser { user { id %s } }
    """ % field

    with pytest.raises(TypeError) as err:
        execute(graph, read(query))

    err.match(
        "Enum 'UserStatus' can not represent value: {!r}".format(status)
    )


def test_root_field_enum():
    def get_statuses(fields):
        return [[v for v in Status] for f in fields]

    graph = Graph([
        Root([
            Field('statuses', Sequence[EnumRef['Status']], get_statuses),
        ]),
    ], enums=[Enum.from_builtin(Status)])

    query = """
    query GetStatuses {
        statuses
    }
    """
    result = execute(graph, read(query))
    assert result.data == {
        'statuses': ['ACTIVE', 'DELETED']
    }


@pytest.mark.parametrize("enum, status", [
    (Enum.from_builtin(Status, 'UserStatus'), Status.DELETED),
    (Enum('UserStatus', ['ACTIVE', 'DELETED']), 'DELETED'),
])
def test_parse_enum_argument(enum, status):
    def link_user(opt):
        if opt['status'] == status:
            return 1
        raise ValueError(
            'Unknown status: {}'.format(opt['status'])
        )

    @listify
    def resolve_user_fields(fields, ids):
        def get_field(fname, id_):
            if fname == 'id':
                return id_
            elif fname == 'status':
                return status

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
    ], enums=[enum])

    result = execute(graph, read("query GetUser { user(status: DELETED) { id status } }"))
    assert result.data == {
        'user': {
            'id': 1,
            'status': 'DELETED',
        }
    }


@pytest.mark.parametrize("enum, status", [
    (Enum.from_builtin(Status, 'UserStatus'), Status.ACTIVE),
    (Enum('UserStatus', ['ACTIVE', 'DELETED']), 'ACTIVE'),
])
def test_parse_enum_argument_default_value(enum, status):
    def link_user(opt):
        if opt['status'] == status:
            return 1
        raise ValueError(
            'Unknown status: {}'.format(opt['status'])
        )

    @listify
    def resolve_user_fields(fields, ids):
        def get_field(fname, id_):
            if fname == 'id':
                return id_
            elif fname == 'status':
                return status

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
                    Option('status', EnumRef['UserStatus'], default=status)
                ]
            ),
        ]),
    ], enums=[enum])

    query = "query GetUser { user { id status } }"

    assert validate(graph, read(query)) == []

    result = execute(graph, read(query))
    assert result.data == {
        'user': {
            'id': 1,
            'status': 'ACTIVE'
        }
    }



@pytest.mark.parametrize("enum", [
    Enum.from_builtin(Status, 'UserStatus'),
    Enum('UserStatus', ['ACTIVE', 'DELETED']),
])
def test_parse_enum_invalid_argument(enum):
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
    ], enums=[enum])

    query = """
        query GetUser { user(status: INVALID) { id } }
    """
    with pytest.raises(TypeError) as err:
        execute(graph, read(query))

    err.match("Enum 'UserStatus' can not represent value: 'INVALID'")
