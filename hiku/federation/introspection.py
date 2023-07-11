from typing import (
    Callable,
    Dict,
    Any,
    List,
    Optional,
)

from hiku.graph import Field, Graph, Link, Node
from hiku.introspection.types import SCALAR

from hiku.introspection.graphql import GraphQLIntrospection
from hiku.introspection.graphql import AsyncGraphQLIntrospection
from hiku.types import String, TypeRef


def _obj(name: str) -> Dict:
    return {"kind": "OBJECT", "name": name, "ofType": None}


def _non_null(t: Any) -> Dict:
    return {"kind": "NON_NULL", "name": None, "ofType": t}


def _union(name: str, possible_types: Optional[List] = None) -> Dict:
    return {"kind": "UNION", "name": name, "possibleTypes": possible_types}


def _field(name: str, type_: Dict, **kwargs: Any) -> Dict:
    data: Dict = {
        "args": [],
        "deprecationReason": None,
        "description": None,
        "isDeprecated": False,
        "name": name,
        "type": type_,
    }
    data.update(kwargs)
    return data


def _seq_of_nullable(_type: Dict) -> Dict:
    return {
        "kind": "NON_NULL",
        "name": None,
        "ofType": {"kind": "LIST", "name": None, "ofType": _type},
    }


def _seq_of(_type: Dict) -> Dict:
    return _seq_of_nullable({"kind": "NON_NULL", "name": None, "ofType": _type})


def _ival(name: str, type_: Dict, **kwargs: Any) -> Any:
    data = {
        "name": name,
        "type": type_,
        "description": None,
        "defaultValue": None,
    }
    data.update(kwargs)
    return data


def _type(name: str, kind: str, **kwargs: Any) -> Dict:
    data: Dict = {
        "description": None,
        "enumValues": [],
        "fields": [],
        "inputFields": [],
        "interfaces": [],
        "kind": kind,
        "name": name,
        "possibleTypes": [],
    }
    data.update(**kwargs)
    return data


def _is_field_hidden_wrapper(func: Callable) -> bool:
    def wrapper(field: Field):
        if field.name == "_entities":
            return False
        if field.name == "_service":
            return False

        return func(field)

    return wrapper


class BaseFederatedGraphQLIntrospection(GraphQLIntrospection):
    def __init__(
        self,
        query_graph: Graph,
        mutation_graph: Optional[Graph] = None,
    ) -> None:
        super().__init__(query_graph, mutation_graph)
        self.schema.scalars = self.schema.scalars + (
            SCALAR("_Any"),
            SCALAR("_FieldSet"),
        )
        self.schema.nodes_map["_Service"] = Node(
            "_Service", [Field("sdl", String, lambda: None)]
        )
        self.schema.is_field_hidden = _is_field_hidden_wrapper(
            self.schema.is_field_hidden
        )
        self.schema.nodes_map["Query"].fields.append(
            Link("_service", TypeRef["_Service"], lambda: None, requires=None)
        )


class FederatedGraphQLIntrospection(BaseFederatedGraphQLIntrospection):
    """
    Federation-aware introspection for Federation
    https://www.apollographql.com/docs/federation/federation-spec/#federation-schema-specification
    """

    __directives__ = GraphQLIntrospection.__directives__


class AsyncFederatedGraphQLIntrospection(
    FederatedGraphQLIntrospection, AsyncGraphQLIntrospection
):
    """Adds GraphQL introspection into asynchronous federated graph"""
