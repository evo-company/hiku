from typing import Any, Dict, List, Union

from hiku.graph import Graph

from hiku.federation.directive import FieldSet, Key
from hiku.utils import ImmutableDict, to_immutable_dict


def get_keys(graph: Graph, typename: str) -> List[FieldSet]:
    """Get all 'key' directives fields"""
    node = graph.nodes_map[typename]
    return [d.fields for d in node.directives if isinstance(d, Key)]


Scalar = Any


def get_representation_ident(
    representation: Dict, graph: Graph
) -> Union[Scalar, ImmutableDict]:
    typename = representation["__typename"]
    for key in get_keys(graph, typename):
        if key in representation:
            # If it's a single field name, then extract the value
            return representation[key]

    # If it's a multi-field or composite key, then the whole representation
    # (except __typename) must be an ident.
    # This works similar to how Link(require=[]) works.
    rep = {k: v for k, v in representation.items() if k != "__typename"}
    return to_immutable_dict(rep)
