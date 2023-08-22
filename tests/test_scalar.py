from datetime import datetime

import pytest

from hiku.denormalize.graphql import DenormalizeGraphQL
from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.graph import Field, Graph, Link, Node, Nothing, Option, Root
from hiku.scalar import DateTime, Scalar
from hiku.types import Integer, Optional, Sequence, TypeRef
from hiku.utils import listify
from hiku.readers.graphql import read
from hiku.validate.graph import GraphValidationError


def execute(graph, query):
    engine = Engine(SyncExecutor())
    result = engine.execute_query(graph, query, {})
    return DenormalizeGraphQL(graph, result, "query").process(query)


class SomeType:
    ...

def test_validate_graph_invalid_scalars():
    with pytest.raises(GraphValidationError) as err:
        Graph([
            Node('User', [
                Field('id', Integer, lambda: None),
                Field('dateCreated', SomeType, lambda: None),
            ]),
            Root([
                Link('user', Optional[TypeRef['User']], lambda: None, requires=None),
            ]),
        ])

    assert err.value.errors == [
        'Field "User.dateCreated" has type "<class \'tests.test_scalar.SomeType\'>" but Hiku does not support it.',
    ]


def test_validate_graph_not_defined_scalars():

    class SomeType(Scalar):
        ...

    with pytest.raises(GraphValidationError) as err:
        Graph([
            Node('User', [
                Field('id', Integer, lambda: None),
                Field('dateCreated', SomeType, lambda: None),
            ]),
            Root([
                Link('user', Optional[TypeRef['User']], lambda: None, requires=None),
            ]),
        ])

    assert err.value.errors == [
        'Field "User.dateCreated" has type "<class \'tests.test_scalar.test_validate_graph_not_defined_scalars.<locals>.SomeType\'>" but no scalar is defined for it. '
        'Maybe you forgot to add new scalar to Graph(..., scalars)?',
    ]


DATE_CREATED = datetime(2023, 6, 15, 12, 30, 59, 0)
DATE_CREATED_STR = '2023-06-15T12:30:59'  # TODO: check timezone


def test_serialize_scalar_field_correct():
    @listify
    def resolve_user_fields(fields, ids):
        def get_field(fname, id_):
            if fname == 'id':
                return id_
            elif fname == 'dateCreated':
                return DATE_CREATED
            elif fname == 'dateCreatedMany':
                return [DATE_CREATED]
            elif fname == 'dateCreatedManyOptional':
                return [DATE_CREATED, None]
            elif fname == 'dateCreatedMaybe':
                return None
            elif fname == 'dateCreatedMaybeSequence':
                return []

        for id_ in ids:
            yield [get_field(f.name, id_) for f in fields]

    graph = Graph([
        Node('User', [
            Field('id', Integer, resolve_user_fields),
            Field('dateCreated', DateTime, resolve_user_fields),
            Field('dateCreatedMany', Sequence[DateTime], resolve_user_fields),
            Field('dateCreatedManyOptional', Sequence[Optional[DateTime]], resolve_user_fields),
            Field('dateCreatedMaybe', Optional[DateTime], resolve_user_fields),
            Field('dateCreatedMaybeSequence', Optional[Sequence[DateTime]], resolve_user_fields),
        ]),
        Root([
            Link('user', Optional[TypeRef['User']], lambda: 1, requires=None),
        ]),
    ], scalars=[DateTime])

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
    assert result == {
        'user': {
            'id': 1,
            'dateCreated': DATE_CREATED_STR,
            'dateCreatedMany': [DATE_CREATED_STR],
            'dateCreatedManyOptional': [DATE_CREATED_STR, None],
            'dateCreatedMaybe': None,
            'dateCreatedMaybeSequence': [],
        }
    }


def test_parse_scalar_input_correct():
    @listify
    def resolve_user_fields(fields, ids):
        def get_field(fname, id_):
            if fname == 'id':
                return id_
            elif fname == 'dateCreated':
                return DATE_CREATED

        for id_ in ids:
            yield [get_field(f.name, id_) for f in fields]

    def link_user(opts):
        if opts['dateCreated'] == DATE_CREATED:
            return 1

        return Nothing

    graph = Graph([
        Node('User', [
            Field('id', Integer, resolve_user_fields),
            Field('dateCreated', DateTime, resolve_user_fields),
        ]),
        Root([
            Link(
                'user',
                Optional[TypeRef['User']],
                link_user,
                requires=None,
                options=[
                    Option('dateCreated', DateTime),
                    Option('dateCreatedMany', Sequence[DateTime]),
                    Option('dateCreatedMaybe', Optional[DateTime]),
                ]
            ),
        ]),
    ], scalars=[DateTime])

    query = """
    query GetUser {
      user(dateCreated: "%s", dateCreatedMany: ["%s"], dateCreatedMaybe: null) {
        id
        dateCreated
      }
    }
    """ % (DATE_CREATED_STR, DATE_CREATED_STR)

    result = execute(graph, read(query))
    assert result == {
        'user': {
            'id': 1,
            'dateCreated': DATE_CREATED_STR,
        }
    }
