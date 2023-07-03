import typing as t

from hiku.graph import Graph, Union
from hiku.query import Node, QueryTransformer


class SplitUnionByNodes(QueryTransformer):
    """
    Split query node into graph nodes by union types with keys as node names.

    Useful when you need to find graph nodes by its name.

    :return: dict with graph nodes as values and graph node names as keys.
    """

    def __init__(self, graph: Graph, union: Union) -> None:
        self._graph = graph
        self._union = union

    def split(self, obj: Node) -> t.Dict[str, Node]:
        types = [self._graph.nodes_map[type_] for type_ in self._union.types]

        nodes = {}
        for type_ in types:
            nodes[type_.name] = obj.copy(
                fields=[f for f in obj.fields if f.name in type_.fields_map]
            )

        return nodes
