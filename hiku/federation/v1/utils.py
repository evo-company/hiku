from typing import List

from hiku.graph import Graph

from hiku.federation.v1.directive import Key


def get_keys(graph: Graph, typename: str) -> List[str]:
    """Get all 'key' directives fields"""
    node = graph.nodes_map[typename]
    return [d.input_args['fields'] for d in node.directives if isinstance(d, Key)]
