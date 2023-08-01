from datetime import datetime

import pytest

from hiku.denormalize.graphql import DenormalizeGraphQL
from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.graph import Field, Graph, Link, Node, Option, Root
from hiku.scalar import DateTime
from hiku.types import Integer, Optional, Sequence, TypeRef
from hiku.utils import listify
from hiku.readers.graphql import read
from hiku.validate.graph import GraphValidationError


def execute(graph, query):
    engine = Engine(SyncExecutor())
    result = engine.execute(graph, query, {})
    return DenormalizeGraphQL(graph, result, "query").process(query)


class SomeType:
    ...

def test_validate_graph_scalars():
    with pytest.raises(GraphValidationError) as err:
        Graph([
            Node('User', [
                Field('id', Integer, lambda: None),
                Field('dateCreated', SomeType , lambda: None),
            ]),
            Root([
                Link('user', Optional[TypeRef['User']], lambda: None, requires=None),
            ]),
        ])

    assert err.value.errors == [
        'Field "User.dateCreated" has type "<class \'tests.test_scalar.SomeType\'>" but no scalar is defined for it',
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

        for id_ in ids:
            yield [get_field(f.name, id_) for f in fields]

    graph = Graph([
        Node('User', [
            Field('id', Integer, resolve_user_fields),
            Field('dateCreated', datetime, resolve_user_fields),
        ]),
        Root([
            Link('user', Optional[TypeRef['User']], lambda: 1, requires=None),
        ]),
    ], scalars={
        datetime: DateTime
    })

    query = """
    query GetUser {
      user {
        id
        dateCreated
      }
    }
    """
    result = execute(graph, read(query))
    assert result == {
        'user': {
            'id': 1,
            'dateCreated': DATE_CREATED_STR,
        }
    }
