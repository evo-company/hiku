from typing import (
    Dict,
    Any,
    List,
    Optional,
)

from ..graph import Graph
from ..query import Node as QueryNode

from ..introspection.types import NON_NULL, SCALAR
from ..introspection.graphql import Directive, GraphQLIntrospection
from ..introspection.graphql import AsyncGraphQLIntrospection

from .utils import get_keys


_DIRECTIVES = (
    # https://www.apollographql.com/docs/federation/federation-spec/#key
    Directive(
        name='key',
        locations=['OBJECT', 'INTERFACE'],
        description=(
            'The @key directive is used to indicate a combination '
            'of fields that can be used to uniquely identify and '
            'fetch an object or interface.'
        ),
        args=[
            Directive.Argument(
                name='fields',
                type_ident=NON_NULL(SCALAR('_FieldSet')),
                description=(
                    'A combination of fields that can be used to uniquely '
                    'identify and fetch an object or interface'
                ),
                default_value=None,
            ),
        ],
    ),
    # https://www.apollographql.com/docs/federation/federation-spec/#provides
    Directive(
        name='provides',
        locations=['FIELD_DEFINITION'],
        description=(
            'The @provides directive is used to annotate the expected returned '
            'fieldset from a field on a base type that is guaranteed to be '
            'selectable by the gateway'
        ),
        args=[
            Directive.Argument(
                name='fields',
                type_ident=NON_NULL(SCALAR('_FieldSet')),
                description=(
                    'Expected returned fieldset from a field on a base type '
                    'that is guaranteed to be selectable by the gateway'
                ),
                default_value=None,
            ),
        ],
    ),
    # https://www.apollographql.com/docs/federation/federation-spec/#requires
    Directive(
        name='requires',
        locations=['FIELD_DEFINITION'],
        description=(
            'The @requires directive is used to annotate the required input '
            'fieldset from a base type for a resolver.'
        ),
        args=[
            Directive.Argument(
                name='fields',
                type_ident=NON_NULL(SCALAR('_FieldSet')),
                description=(
                    'The required input fieldset from a base type for a '
                    'resolver'
                ),
                default_value=None,
            ),
        ],
    ),
    # https://www.apollographql.com/docs/federation/federation-spec/#external
    Directive(
        name='external',
        locations=['FIELD_DEFINITION'],
        description=(
            'The @external directive is used to mark a field '
            'as owned by another service.'
        ),
        args=[],
    ),
)


def is_introspection_query(query: QueryNode) -> bool:
    return '__schema' in query.fields_map


def _obj(name: str) -> Dict:
    return {'kind': 'OBJECT', 'name': name, 'ofType': None}


def _non_null(t: Any) -> Dict:
    return {'kind': 'NON_NULL', 'name': None, 'ofType': t}


def _union(name: str, possible_types: Optional[List] = None) -> Dict:
    return {
        'kind': 'UNION',
        'name': name,
        'possibleTypes': possible_types
    }


def _field(name: str, type_: Dict, **kwargs: Any) -> Dict:
    data: Dict = {
        'args': [],
        'deprecationReason': None,
        'description': None,
        'isDeprecated': False,
        'name': name,
        'type': type_
    }
    data.update(kwargs)
    return data


def _seq_of_nullable(_type: Dict) -> Dict:
    return {'kind': 'NON_NULL', 'name': None,
            'ofType': {'kind': 'LIST', 'name': None,
                       'ofType': _type}}


def _seq_of(_type: Dict) -> Dict:
    return _seq_of_nullable({'kind': 'NON_NULL', 'name': None,
                            'ofType': _type})


def _ival(name: str, type_: Dict, **kwargs: Any) -> Any:
    data = {
        'name': name,
        'type': type_,
        'description': None,
        'defaultValue': None,
    }
    data.update(kwargs)
    return data


def _type(name: str, kind: str, **kwargs: Any) -> Dict:
    data: Dict = {
        'description': None,
        'enumValues': [],
        'fields': [],
        'inputFields': [],
        'interfaces': [],
        'kind': kind,
        'name': name,
        'possibleTypes': [],
    }
    data.update(**kwargs)
    return data


def extend_with_federation(graph: Graph, data: dict) -> None:
    union_types = []
    for node in graph.nodes:
        if get_keys(graph, node.name):
            union_types.append(_obj(node.name))

    data['__schema']['types'].append(_type('_Any', 'SCALAR'))
    data['__schema']['types'].append(_type('_FieldSet', 'SCALAR'))
    data['__schema']['types'].append(
        _type('_Entity', 'UNION', possibleTypes=union_types)
    )
    data['__schema']['types'].append(
        _type('_Service', 'OBJECT',
              fields=[_field('sdl', _type('String', 'SCALAR'))])
    )

    entities_field = _field(
        '_entities',
        _seq_of_nullable(_union('_Entity', union_types)),
        args=[_ival('representations', _seq_of(_type('_Any', 'SCALAR')))]
    )

    service_field = _field(
        '_service',
        _non_null(_obj('_Service')),
    )
    for t in data['__schema']['types']:
        if t['kind'] == 'OBJECT' and t['name'] == 'Query':
            t['fields'].append(entities_field)
            t['fields'].append(service_field)


class FederatedGraphQLIntrospection(GraphQLIntrospection):
    """
    Federation-aware introspection
    https://www.apollographql.com/docs/federation/federation-spec/#federation-schema-specification
    """
    __directives__ = GraphQLIntrospection.__directives__ + _DIRECTIVES


class AsyncFederatedGraphQLIntrospection(
    FederatedGraphQLIntrospection,
    AsyncGraphQLIntrospection
):
    """Adds GraphQL introspection into asynchronous federated graph"""
