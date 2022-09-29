from typing import (
    Optional,
    TYPE_CHECKING,
)

from graphql.language import ast

if TYPE_CHECKING:
    from hiku.directives import QueryDirective


class Extension:
    def on_directive_parsing(
        self, obj: ast.DirectiveNode, visitor
    ) -> Optional['QueryDirective']:
        ...
