from dataclasses import dataclass
from typing import (
    Optional,
    Dict,
)

from graphql.language import ast

from hiku.graph import Graph
from hiku.query import Node


@dataclass
class ExecutionContext:
    query: str  # TODO: maybe rename into `query_source`?
    variables: Optional[Dict]
    operation_name: Optional[str]
    query_graph: 'Graph'
    mutation_graph: Optional['Graph'] = None
    graphql_document: Optional[ast.DocumentNode] = None
    query_node: Optional[Node] = None
    # TODO: do we need graph and mutation graph here ?
