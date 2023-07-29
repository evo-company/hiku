import typing as t
from itertools import chain

from hiku.graph import Graph
from hiku.query import Node


class SplitInterfaceQueryByNodes:
    """
    Split query node into query nodes by interface types with keys
    as graph node names.

    Useful when you need to get query nodes for interface

    :return: dict with query nodes as values and graph node names as keys.
    """

    def __init__(self, graph: Graph) -> None:
        self._graph = graph

    def split(self, obj: Node) -> t.Dict[str, Node]:
        types = [
            self._graph.nodes_map[type_]
            for type_ in set(
                chain.from_iterable(self._graph.interfaces_types.values())
            )
        ]

        nodes = {}
        for type_ in types:
            fields = []
            for field in obj.fields:
                if field.name in type_.fields_map and (
                    field.parent_type == type_.name or field.parent_type is None
                ):
                    fields.append(field)

            nodes[type_.name] = obj.copy(fields=fields)

        return nodes
