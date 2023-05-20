from collections import deque

from hiku.denormalize.graphql import DenormalizeGraphQL
from hiku.graph import Graph
from hiku.result import Proxy


class DenormalizeEntityGraphQL(DenormalizeGraphQL):
    def __init__(
        self, graph: Graph, result: Proxy, root_type_name: str
    ) -> None:
        super().__init__(graph, result, root_type_name)
        self._type = deque([graph.__types__[root_type_name]])
