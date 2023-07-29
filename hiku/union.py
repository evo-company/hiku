import typing as t

from hiku.graph import Graph, Union
from hiku.query import Node


class SplitUnionQueryByNodes:
    """
    Split query node into query nodes by union types with keys
    as graph node names.

    Useful when you need to get query nodes for unions

    :return: dict with query nodes as values and graph node names as keys.
    """

    def __init__(self, graph: Graph, union: Union) -> None:
        self._graph = graph
        self._union = union

    def split(self, obj: Node) -> t.Dict[str, Node]:
        types = [self._graph.nodes_map[type_] for type_ in self._union.types]

        nodes = {}
        for type_ in types:
            fields = []
            for field in obj.fields:
                if (
                    field.parent_type == type_.name
                    and field.name in type_.fields_map
                ):
                    fields.append(field)

            # TODO: do we need to add all nodes even if node is empty ?
            nodes[type_.name] = obj.copy(fields=fields)

        return nodes
