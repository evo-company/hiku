from typing import Iterator

from hiku.context import ExecutionContext
from hiku.extensions.base_extension import Extension
from hiku.extensions.base_validator import QueryValidator
from hiku.graph import Graph
from hiku.query import Field, Link, Node


class _QueryAliasesValidator(QueryValidator):
    max_aliases: int

    """
    :param max_aliases: maximum allowed number of aliases in a query
    """

    def __init__(self, max_aliases: int):
        self.max_aliases = max_aliases
        self._count = 0

    def validate(self, query: Node, graph: Graph) -> list[str]:
        count = self.calculate(query)
        if count > self.max_aliases:
            return [
                f"Query uses {count} aliases which exceeds maximum "
                f"allowed number of aliases {self.max_aliases}"
            ]

        return []

    def calculate(self, obj: Node) -> int:
        self._count = 0
        self.visit(obj)
        return self._count

    def visit_field(self, obj: Field) -> None:
        if obj.alias is not None:
            self._count += 1

    def visit_link(self, obj: Link) -> None:
        if obj.alias is not None:
            self._count += 1
        super().visit_link(obj)


class QueryAliasesValidator(Extension):
    """Use this extension to limit the maximum allowed number of aliases.

    Repeating a field under many aliases is a common way to amplify the cost
    of a single request, so each client app should cap it.

    Example:
        Schema(executor, graph, extensions=[
            QueryAliasesValidator(max_aliases=10),
        ])

    """

    def __init__(self, max_aliases: int) -> None:
        self._validator = _QueryAliasesValidator(max_aliases)

    def on_validate(
        self, execution_context: ExecutionContext
    ) -> Iterator[None]:
        execution_context.validators = execution_context.validators + tuple(
            [self._validator]
        )

        yield
