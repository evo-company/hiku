from typing import Iterator, List

from hiku.context import ExecutionContext
from hiku.extensions.base_extension import Extension
from hiku.extensions.base_validator import QueryValidator
from hiku.graph import Graph
from hiku.query import Field, Link, Node


def is_introspection_key(key: str) -> bool:
    """See: https://spec.graphql.org/June2018/#sec-Schema"""
    return key.startswith("__")


class _QueryDepthValidator(QueryValidator):
    max_depth: int

    """
    :param max_depth: maximum allowed query depth
    """

    def __init__(self, max_depth: int):
        self.max_depth = max_depth
        self._current_depth = 0
        self._final_depth = 0

    def validate(self, query: Node, graph: Graph) -> List[str]:
        depth = self.calculate(query)
        if depth > self.max_depth:
            return [
                f"Query depth {depth} exceeds maximum "
                f"allowed depth {self.max_depth}"
            ]

        return []

    def calculate(self, obj: Node) -> int:
        self.visit(obj)
        return self._final_depth

    def visit_field(self, obj: Field) -> None:
        pass  # Do nothing for individual fields.

    def visit_link(self, obj: Link) -> None:
        if not is_introspection_key(obj.name):
            super().visit_link(obj)

    def visit_node(self, obj: Node) -> None:
        self._current_depth += 1
        self._final_depth = max(self._final_depth, self._current_depth)
        super().visit_node(obj)
        self._current_depth -= 1


class QueryDepthValidator(Extension):
    """Use this extension to limit the maximum allowed query depth.

    Example:
        Endpoint(engine, graph, extensions=[
            QueryDepthValidator(max_depth=10),
        ])

    """

    def __init__(self, max_depth: int):
        self._validator = _QueryDepthValidator(max_depth)

    def on_validate(
        self, execution_context: ExecutionContext
    ) -> Iterator[None]:
        execution_context.validators = execution_context.validators + tuple(
            [self._validator]
        )

        yield
