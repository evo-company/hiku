from typing import List

from hiku.graph import Graph


def get_keys(graph: Graph, typename: str) -> List[int]:
    """Get all 'key' directives fields"""
    node = graph.nodes_map[typename]
    return [
        d.args_map['fields'].value for d in
        filter(lambda d: d.name == 'key', node.directives)
    ]
