import typing as t

from hiku.denormalize.graphql import DenormalizeGraphQL
from hiku.graph import Graph
from hiku.result import Proxy
from hiku.types import Record, Sequence, TypeRef


class DenormalizeEntityGraphQL(DenormalizeGraphQL):
    def __init__(
        self, graph: Graph, result: Proxy, entity_type_name: str
    ) -> None:
        super().__init__(graph, result, "Query")
        t.cast(Record, self._type[-1]).__field_types__["_entities"] = Sequence[
            TypeRef[entity_type_name]
        ]
