from typing import List

from hiku.graph import Graph, Node

from hiku.federation.directive import FieldSet, Key


def get_keys(graph: Graph, typename: str) -> List[FieldSet]:
    """Get all 'key' directives fields"""
    node = graph.nodes_map[typename]
    return [d.fields for d in node.directives if isinstance(d, Key)]


def get_entity_types(nodes: List[Node], federation_version: int) -> List[str]:
    entity_nodes = set()
    for node in nodes:
        if node.name is not None:
            for directive in node.directives:
                if isinstance(directive, Key):
                    if not directive.resolvable and federation_version == 2:
                        continue
                    entity_nodes.add(node.name)

    return list(sorted(entity_nodes))
