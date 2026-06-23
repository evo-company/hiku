from collections import defaultdict
from typing import Iterator

from hiku.context import ExecutionContext
from hiku.extensions.base_extension import Extension
from hiku.extensions.base_validator import QueryValidator
from hiku.graph import Graph
from hiku.query import Field, FieldOrLink, Fragment, Link, Node


class _AliasLimitExceeded(Exception):
    pass


class _QueryAliasesValidator(QueryValidator):
    max_aliases: int

    """
    :param max_aliases: maximum allowed number of aliases to the same field
        within a single selection set
    """

    def __init__(self, max_aliases: int) -> None:
        self.max_aliases = max_aliases
        self._counts: dict[str, int] = {}

    def validate(self, query: Node, graph: Graph) -> list[str]:
        try:
            self.visit(query)
        except _AliasLimitExceeded as e:
            return [str(e)]
        return []

    def visit_node(self, obj: Node) -> None:
        parent_counts = self._counts
        self._counts = defaultdict(int)
        try:
            super().visit_node(obj)
            for fragment in obj.fragments:
                self.visit(fragment)
        finally:
            self._counts = parent_counts

    def visit_fragment(self, obj: Fragment) -> None:
        # Fragment fields merge into the parent selection set, so count them
        # against the current scope instead of opening a new one.
        node = obj.node
        for item in node.fields:
            self.visit(item)
        for fragment in node.fragments:
            self.visit(fragment)

    def visit_field(self, obj: Field) -> None:
        self._count_alias(obj)

    def visit_link(self, obj: Link) -> None:
        self._count_alias(obj)
        super().visit_link(obj)

    def _count_alias(self, field: FieldOrLink) -> None:
        if field.alias is None:
            return
        self._counts[field.name] += 1
        if self._counts[field.name] > self.max_aliases:
            raise _AliasLimitExceeded(
                f"Field '{field.name}' is aliased more than "
                f"{self.max_aliases} times"
            )


class QueryAliasesValidator(Extension):
    """Limit how many times the same field may be aliased in a selection set.

    Requesting the same field under many aliases is a common way to amplify the
    cost of a single request, so each client app should cap it. If any field is
    aliased more than ``max_aliases`` times within a single selection set, the
    request is rejected with a validation error.

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
