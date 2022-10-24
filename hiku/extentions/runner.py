from typing import (
    List,
    Union,
    Type,
    TYPE_CHECKING,
)

from graphql.language import ast

from hiku.extentions import (
    Extension,
)
from hiku.extentions.cached_directive import CachedDirectiveExt
from hiku.extentions.context import ExecutionContext

if TYPE_CHECKING:
    from hiku.readers.graphql import SelectionSetVisitMixin


DEFAULT_EXTENSIONS = [
    CachedDirectiveExt,
]


class ParsingContextManager:
    def __init__(self, extensions):
        self.extensions = extensions

    def __enter__(self):
        for extension in self.extensions:
            extension.on_parsing_start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        for extension in self.extensions:
            extension.on_parsing_end()

    # TODO: support async


class DirectivesContextManager:
    def __init__(self, extensions, obj, visitor):
        self.extensions = extensions
        self.obj = obj
        self.visitor = visitor
        self.directives = []

    def __enter__(self):
        if not self.obj.directives:
            return self

        for extension in self.extensions:
            directive = extension.on_directives(
                self.obj.directives, self.visitor
            )
            if directive:
                self.directives.append(directive)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ...


class ExtensionsRunner:
    def __init__(
        self,
        execution_context: ExecutionContext,
        extensions: List[Union[Type[Extension], Extension]]
    ) -> None:
        self.execution_context = execution_context

        init_extensions = []
        for ext in extensions + DEFAULT_EXTENSIONS:
            if isinstance(ext, Extension):
                ext.execution_context = execution_context
                init_extensions.append(ext)
            else:
                init_extensions.append(ext(execution_context=execution_context))

        self.extensions = init_extensions

    def parsing(self):
        return ParsingContextManager(self.extensions)

    def directives(self, obj: ast.FieldNode, visitor: 'SelectionSetVisitMixin'):
        return DirectivesContextManager(self.extensions, obj, visitor)
