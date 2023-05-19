from typing import List

from hiku.graph import Graph
from hiku.query import Node
from hiku.validate.query import validate as validate_query


def validate(graph: Graph, query: Node) -> List[str]:
    if "_entities" in query.fields_map or "_service" in query.fields_map:
        return []

    return validate_query(graph, query)
