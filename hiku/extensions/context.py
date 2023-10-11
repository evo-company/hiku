from typing import Callable, Dict, Iterator

from hiku.context import ExecutionContext
from hiku.extensions.base_extension import Extension, ExtensionFactory


class _CustomContextImpl(Extension):
    def __init__(
        self,
        get_context: Callable[[ExecutionContext], Dict],
    ):
        self.get_context = get_context

    def on_execute(self) -> Iterator[None]:
        self.execution_context.context = self.get_context(
            self.execution_context
        )
        yield


class CustomContext(ExtensionFactory):
    ext_class = _CustomContextImpl

    def __init__(self, get_context: Callable[[ExecutionContext], Dict]):
        super().__init__(get_context)
