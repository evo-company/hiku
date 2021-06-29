from typing import List

from ..graph import Graph

from .directive import Key


def get_keys(graph: Graph, typename: str) -> List[int]:
    """Get all 'key' directives fields"""
    node = graph.nodes_map[typename]
    return [d.fields for d in node.directives if isinstance(d, Key)]
