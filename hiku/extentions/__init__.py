from typing import (
    Optional,
    List,
    TYPE_CHECKING,
)

from graphql.language import ast

from hiku.extentions.context import ExecutionContext

if TYPE_CHECKING:
    from hiku.directives import (
        QueryDirective,
    )


class Extension:
    execution_context: ExecutionContext

    def __init__(self, *, execution_context: ExecutionContext = None) -> None:
        self.execution_context = execution_context

    def on_parsing_start(self) -> None:
        pass

    def on_parsing_end(self) -> None:
        pass

    def on_directives(
        self, directives: List[ast.DirectiveNode], visitor
    ) -> Optional['QueryDirective']:
        ...
