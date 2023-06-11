from typing import Any, List

from hiku.graph import Graph, Node

from hiku.federation.directive import FieldSet, Key
from hiku.utils import ImmutableDict, to_immutable_dict


def get_keys(graph: Graph, typename: str) -> List[FieldSet]:
    """Get all 'key' directives fields"""
    node = graph.nodes_map[typename]
    return [d.fields for d in node.directives if isinstance(d, Key)]


def get_entity_types(nodes: List[Node]) -> List[str]:
    entity_nodes = set()
    for node in nodes:
        if node.name is not None:
            for directive in node.directives:
                if isinstance(directive, Key):
                    entity_nodes.add(node.name)

    return list(sorted(entity_nodes))


def representation_to_ident(representation: dict) -> ImmutableDict[str, Any]:
    """Convert representation to ident.
    Ident is a immutable dict that can be used as a key in a dict."""
    return to_immutable_dict(representation)
