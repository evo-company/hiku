from typing import (
    List,
    Optional,
    TYPE_CHECKING,
)

from graphql.language import ast

from hiku.directives import (
    QueryDirective,
    get_directive,
    Cached,
)
from hiku.extentions import Extension

if TYPE_CHECKING:
    from hiku.readers.graphql import SelectionSetVisitMixin


class CachedDirectiveExt(Extension):
    def on_directives(
        self,
        directives: List[ast.DirectiveNode],
        visitor: 'SelectionSetVisitMixin'
    ) -> Optional[QueryDirective]:
        obj = get_directive('cached', directives)
        if not obj:
            return None

        if obj.name.value != 'cached':
            return None

        if len(obj.arguments) != 1:
            raise TypeError('@cached directive accepts exactly one '
                            'argument, {} provided'
                            .format(len(obj.arguments)))
        arg = obj.arguments[0]
        if arg.name.value != 'ttl':
            raise TypeError('@cached directive does not accept "{}" '
                            'argument'
                            .format(arg.name.value))
        ttl = visitor.visit(arg.value)  # type: ignore[attr-defined]
        if not isinstance(ttl, int):
            raise TypeError('@cached ttl argument must be an integer')

        return Cached(ttl)
