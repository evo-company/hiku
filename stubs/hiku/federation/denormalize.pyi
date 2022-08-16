from hiku.denormalize.graphql import DenormalizeGraphQL as DenormalizeGraphQL
from hiku.graph import Graph as Graph
from hiku.result import Proxy as Proxy

class DenormalizeEntityGraphQL(DenormalizeGraphQL):
    def __init__(self, graph: Graph, result: Proxy, root_type_name: str) -> None: ...
