from typing import Any, List

from hiku.graph import Graph

from hiku.federation.directive import FieldSet, Key
from hiku.utils import ImmutableDict, to_immutable_dict


def get_keys(graph: Graph, typename: str) -> List[FieldSet]:
    """Get all 'key' directives fields"""
    node = graph.nodes_map[typename]
    return [d.fields for d in node.directives if isinstance(d, Key)]


def representation_to_ident(representation: dict) -> ImmutableDict[str, Any]:
    """Convert representation to ident.
    Ident is a immutable dict that can be used as a key in a dict."""
    return to_immutable_dict(representation, exclude_keys={"__typename"})
