from __future__ import annotations

import contextlib
import inspect
from asyncio import iscoroutinefunction

from types import TracebackType
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Sequence,
    TYPE_CHECKING,
    Type,
    TypeVar,
    Union,
)

if TYPE_CHECKING:
    from hiku.context import ExecutionContext


T = TypeVar("T")

AwaitableOrValue = Union[Awaitable[T], T]
AsyncIteratorOrIterator = Union[AsyncIterator[T], Iterator[T]]
Hook = Callable[["Extension"], AsyncIteratorOrIterator[None]]


class Extension:
    execution_context: ExecutionContext

    def __init__(self, *, execution_context: Optional[ExecutionContext] = None):
        # execution_context will be set during ExtensionsManager initialization
        # it is safe to assume that it will be not None
        self.execution_context = execution_context  # type: ignore[assignment]

    def on_graph(self) -> AsyncIteratorOrIterator[None]:
        """Called before the graph transformation step"""
        yield None

    def on_dispatch(self) -> AsyncIteratorOrIterator[None]:
        """Called before and after the dispatch step"""
        yield None

    def on_operation(self) -> AsyncIteratorOrIterator[None]:
        """Called before and after the operation step"""
        yield None

    def on_parse(self) -> AsyncIteratorOrIterator[None]:
        """Called before and after the parsing step"""
        yield None

    def on_validate(self) -> AsyncIteratorOrIterator[None]:
        """Called before and after the validation step"""
        yield None

    def on_execute(self) -> AsyncIteratorOrIterator[None]:
        """Called before and after the execution step"""
        yield None


class ExtensionsManager:
    def __init__(
        self,
        execution_context: ExecutionContext,
        extensions: Sequence[Union[Type[Extension], Extension]],
    ):
        self.execution_context = execution_context

        if not extensions:
            extensions = []

        init_extensions: List[Extension] = []

        for extension in extensions:
            if isinstance(extension, Extension):
                extension.execution_context = execution_context
                init_extensions.append(extension)
            else:
                init_extensions.append(
                    extension(execution_context=execution_context)
                )

        self.extensions = init_extensions

    def graph(self) -> "ExtensionContextManagerBase":
        return ExtensionContextManagerBase(
            Extension.on_graph.__name__,
            self.extensions,
        )

    def dispatch(self) -> "ExtensionContextManagerBase":
        return ExtensionContextManagerBase(
            Extension.on_dispatch.__name__,
            self.extensions,
        )

    def parsing(self) -> "ExtensionContextManagerBase":
        return ExtensionContextManagerBase(
            Extension.on_parse.__name__,
            self.extensions,
        )

    def operation(self) -> "ExtensionContextManagerBase":
        return ExtensionContextManagerBase(
            Extension.on_operation.__name__,
            self.extensions,
        )

    def validation(self) -> "ExtensionContextManagerBase":
        return ExtensionContextManagerBase(
            Extension.on_validate.__name__,
            self.extensions,
        )

    def execution(self) -> "ExtensionContextManagerBase":
        return ExtensionContextManagerBase(
            Extension.on_execute.__name__,
            self.extensions,
        )


class WrappedHook(NamedTuple):
    extension: Extension
    initialized_hook: Union[AsyncIterator[None], Iterator[None]]
    is_async: bool


class ExtensionContextManagerBase:
    __slots__ = ("hook_name", "hooks", "deprecation_message", "default_hook")

    def __init__(self, hook_name: str, extensions: List[Extension]):
        self.hook_name = hook_name
        self.hooks: List[WrappedHook] = []
        self.default_hook: Hook = getattr(Extension, self.hook_name)
        for extension in extensions:
            hook = self.get_hook(extension)
            if hook:
                self.hooks.append(hook)

    def get_hook(self, extension: Extension) -> Optional[WrappedHook]:
        hook_fn: Optional[Hook] = getattr(type(extension), self.hook_name)
        hook_fn = hook_fn if hook_fn is not self.default_hook else None

        if hook_fn:
            if inspect.isgeneratorfunction(hook_fn):
                return WrappedHook(extension, hook_fn(extension), False)

            if inspect.isasyncgenfunction(hook_fn):
                return WrappedHook(extension, hook_fn(extension), True)

            if callable(hook_fn):
                return self.from_callable(extension, hook_fn)

            raise ValueError(
                f"Hook {self.hook_name} on {extension} "
                f"must be callable, received {hook_fn!r}"
            )

        return None

    @staticmethod
    def from_callable(
        extension: Extension,
        func: Callable[[Extension], AwaitableOrValue[Any]],
    ) -> WrappedHook:
        if iscoroutinefunction(func):

            async def async_iterator():  # type: ignore[no-untyped-def]
                await func(extension)
                yield

            hook = async_iterator()
            return WrappedHook(extension, hook, True)
        else:

            def iterator():  # type: ignore[no-untyped-def]
                func(extension)
                yield

            hook = iterator()
            return WrappedHook(extension, hook, False)

    def run_hooks_sync(self, is_exit: bool = False) -> None:
        """Run extensions synchronously."""
        ctx = (
            contextlib.suppress(StopIteration, StopAsyncIteration)
            if is_exit
            else contextlib.nullcontext()
        )
        for hook in self.hooks:
            with ctx:
                if hook.is_async:
                    raise RuntimeError(
                        f"Extension hook {hook.extension}.{self.hook_name} "
                        "is async."
                    )
                else:
                    hook.initialized_hook.__next__()  # type: ignore[union-attr]

    def __enter__(self):  # type: ignore[no-untyped-def]
        self.run_hooks_sync()

    def __exit__(  # type: ignore[no-untyped-def]
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ):
        self.run_hooks_sync(is_exit=True)

    # TODO: support async
