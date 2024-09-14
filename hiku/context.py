from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

from graphql.language import ast

from hiku.introspection.graphql import MUTATION_ROOT_NAME, QUERY_ROOT_NAME
from hiku.result import Proxy
from hiku.operation import Operation, OperationType
from hiku.extensions.base_validator import QueryValidator
from hiku.query import Node
from hiku.graph import Graph, GraphTransformer

_type_names: Dict[OperationType, str] = {
    OperationType.QUERY: QUERY_ROOT_NAME,
    OperationType.MUTATION: MUTATION_ROOT_NAME,
}


@dataclass
class ExecutionContext:
    query_src: str
    variables: Optional[Dict[str, Any]]
    context: Dict
    graphql_document: Optional[ast.DocumentNode] = None
    query: Optional[Node] = None
    query_graph: Optional[Graph] = None
    mutation_graph: Optional[Graph] = None
    operation: Optional["Operation"] = None
    """Operation name from request's json operationName"""
    request_operation_name: Optional[str] = None
    result: Optional[Proxy] = None
    """If errors is list, validation was performed"""
    errors: Optional[List[str]] = None

    validators: Tuple[QueryValidator, ...] = field(
        default_factory=lambda: tuple()
    )
    transformers: Tuple["GraphTransformer", ...] = field(
        default_factory=lambda: tuple()
    )

    @property
    def operation_name(self) -> Optional[str]:
        if self.request_operation_name is not None:
            return self.request_operation_name

        if self.operation is None:
            return None

        return self.operation.name

    @property
    def operation_type_name(self) -> str:
        if self.operation is None:
            type_ = OperationType.QUERY
        else:
            type_ = self.operation.type

        return _type_names[type_]

    @property
    def graph(self) -> Graph:
        if self.operation is None:
            # if query ordered we need to execute it on mutation graph
            if self.query and self.query.ordered:
                if self.mutation_graph:
                    return self.mutation_graph

            assert self.query_graph is not None
            return self.query_graph

        if (
            self.operation.type is OperationType.QUERY
            or self.operation.type is None
        ):
            assert self.query_graph is not None
            return self.query_graph
        elif (
            self.operation.type is OperationType.MUTATION
            and self.mutation_graph is not None
        ):
            return self.mutation_graph

        assert self.query_graph is not None
        return self.query_graph


@dataclass
class ExecutionContextFinal(ExecutionContext):
    """Final execution context, after validation and query transformation."""

    operation: "Operation"  # type: ignore[misc]
    query: Node  # type: ignore[misc]
    query_graph: Graph  # type: ignore[misc]
    mutation_graph: Optional[Graph] = None


def create_execution_context(
    query: Union[str, Node, None] = None,
    variables: Optional[Dict] = None,
    operation_name: Optional[str] = None,
    query_graph: Optional[Graph] = None,
    mutation_graph: Optional[Graph] = None,
    context: Optional[Dict] = None,
    **kwargs: Any,
) -> ExecutionContext:
    query_src = None
    query_node = None
    if isinstance(query, str):
        query_src = query
    elif isinstance(query, Node):
        query_node = query
        if "operation" not in kwargs:
            op_type = OperationType.QUERY
            if query.ordered:
                op_type = OperationType.MUTATION
            kwargs["operation"] = Operation(op_type, query)

    return ExecutionContext(
        query_src=query_src or "",
        variables=variables,
        request_operation_name=operation_name,
        context=context or {},
        query_graph=query_graph,
        mutation_graph=mutation_graph,
        query=query_node,
        **kwargs,
    )
