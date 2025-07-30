from __future__ import annotations

import contextlib
import inspect
from asyncio import iscoroutinefunction
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    AsyncIterator,
    Awaitable,
    Callable,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
)

if TYPE_CHECKING:
    from hiku.context import ExecutionContext


T = TypeVar("T")

AwaitableOrValue = Union[Awaitable[T], T]
AsyncIteratorOrIterator = Union[AsyncIterator[T], Iterator[T]]
Hook = Callable[
    ["Extension", "ExecutionContext"], AsyncIteratorOrIterator[None]
]


class Extension:
    """Extension class for hooking into the GraphQL execution lifecycle.

    Extensions allow you to intercept and modify the execution flow at various
    stages of query processing. Each hook is called before and after its
    respective stage, providing opportunities for logging, monitoring,
    validation, and more.

    **Extension Lifecycle Diagram:**

    ```
    Schema Creation
    ┌─────────────────────────────────────────────────────────────┐
    │ on_init() - Called once during schema creation              │
    │ • Add transformers to execution context                     │
    │ • Setup global state, monitoring, etc.                      │
    └─────────────────────────────────────────────────────────────┘

    Query Execution (per request)
    ┌─────────────────────────────────────────────────────────────┐
    │ on_operation() - Wraps entire operation lifecycle           │
    │ ┌─────────────────────────────────────────────────────────┐ │
    │ │ on_parse() - Query parsing and AST transformation     │ │ |
    │ │ • Parse GraphQL string to AST                         │ │ |
    │ │ • Transform AST to Hiku query nodes                   │ │ |
    │ └─────────────────────────────────────────────────────────┘ │
    │ ┌─────────────────────────────────────────────────────────┐ │
    │ │ on_validate() - Query validation                      │ │ |
    │ │ • Validate query against schema                       │ │ |
    │ │ • Check field existence, types, etc.                  │ │ |
    │ │ • Set execution_context.errors if validation fails    │ │ |
    │ └─────────────────────────────────────────────────────────┘ │
    │ ┌─────────────────────────────────────────────────────────┐ │
    │ │ on_execute() - Query execution                        │ │ |
    │ │ • Execute query against data sources                  │ │ |
    │ │ • Resolve fields and relationships                    │ │ |
    │ │ • Set execution_context.result                        │ │ |
    │ │ • Denormalize result                                  │ │ |
    │ └─────────────────────────────────────────────────────────┘ │
    └─────────────────────────────────────────────────────────────┘

    **Hook execution order:**
    1. on_init() - Schema creation (once)
    2. on_operation() - Start of operation
    3.   on_parse() - Query parsing
    4.   on_validate() - Query validation
    5.   on_execute() - Query execution
    6. on_operation() - End of operation

    **ExecutionContext fields availability:**
    - on_init: Basic execution context
    - on_operation:
        before yield: query_src, variables, operation_name, context
        after yield: all fields from execution_context
    - on_parse:
        before yield: all from previous hooks
        after yield: graphql_document (AST), operation, query
    - on_validate:
        before yield: all from previous hooks
        after yield: errors
    - on_execute:
        before yield: all from previous hooks
        after yield: result

    **Hook implementation:**
    Each hook should be implemented as a generator function that yields once:
    ```python
    def on_parse(self, execution_context: ExecutionContext) -> Iterator[None]:
        # Pre-parse logic
        yield  # This is where parsing happens
        # Post-parse logic
    ```
    """

    def on_init(  # type: ignore[return]
        self, execution_context: ExecutionContext
    ) -> AsyncIteratorOrIterator[None]:
        """Called once during schema creation.

        It is a good place to add transformers to the execution context.
        """
        yield None

    def on_operation(  # type: ignore[return]
        self, execution_context: ExecutionContext
    ) -> AsyncIteratorOrIterator[None]:
        """Called before and after the operation step.

        A step happens after `on_init` hook and is active during the next hooks:
        - on_parse
        - on_validate
        - on_execute

        `on_operation` hook is the last hook of entrire operation lifecycle.

        Operation step is a step where the query is executed by schema.

        At this step the:
        - execution_context.query_src (if type str) is set to the query string
        - execution_context.query (if type Node) is set to the query Node
        - execution_context.variables is set to the query variables
        - execution_context.operation_name is set to the query operation name
        - execution_context.query_graph is set to the query graph
        - execution_context.mutation_graph is set to the mutation graph
        - execution_context.context is set to the context from execute argument
        """
        yield None

    def on_parse(  # type: ignore[return]
        self, execution_context: ExecutionContext
    ) -> AsyncIteratorOrIterator[None]:
        """Called before and after the parsing step.

        A step happens inside `on_operation` hook and before `on_validate` hook.

        Parse step is when query string is:
        - parsed into graphql ast and will be assigned to the
          execution_context.graphql_document.
          Note that execution_context.query_src parsed only
          if execution_context.query and execution_context.graphql_document are
          empty.
        - graphql ast is transformed into
          hiku's query ast and Operation type is created and assigned to the
          execution_context.operation.
        """
        yield None

    def on_validate(  # type: ignore[return]
        self, execution_context: ExecutionContext
    ) -> AsyncIteratorOrIterator[None]:
        """Called before and after the validation step.

        A step happens inside `on_operation` hook and before `on_execute` hook.

        Validation step is when hiku query is validated.
        After validation is done, if there are errors, they will be assigned
        to the execution_context.errors.
        If there are already execution_context.errors, then validation will be
        skipped (this can happen if errors attribute was set in any hook before
        or in `on_validate` hook before yield.).
        """
        yield None

    def on_execute(  # type: ignore[return]
        self, execution_context: ExecutionContext
    ) -> AsyncIteratorOrIterator[None]:
        """Called before and after the execution step.

        A step happens inside `on_operation` hook and after `on_validate` hook
        and is the last hook inside `on_operation` hook.

        Execution step is when hiku query is executed by hiku engine.

        After execution, normalized result(Proxy) will be assigned
        to execution_context.result."""
        yield None


class ExtensionsManager:
    """ExtensionManager is a per/dispatch extensions manager.

    It is used to call excensions hooks in the right order.
    """

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
                init_extensions.append(extension)
            else:
                init_extensions.append(extension())

        self.extensions = init_extensions

    def init(self) -> "ExtensionContextManagerBase":
        return ExtensionContextManagerBase(
            Extension.on_init.__name__, self.extensions, self.execution_context
        )

    def operation(self) -> "ExtensionContextManagerBase":
        return ExtensionContextManagerBase(
            Extension.on_operation.__name__,
            self.extensions,
            self.execution_context,
        )

    def parsing(self) -> "ExtensionContextManagerBase":
        return ExtensionContextManagerBase(
            Extension.on_parse.__name__, self.extensions, self.execution_context
        )

    def validation(self) -> "ExtensionContextManagerBase":
        return ExtensionContextManagerBase(
            Extension.on_validate.__name__,
            self.extensions,
            self.execution_context,
        )

    def execution(self) -> "ExtensionContextManagerBase":
        return ExtensionContextManagerBase(
            Extension.on_execute.__name__,
            self.extensions,
            self.execution_context,
        )


class WrappedHook(NamedTuple):
    extension: Extension
    initialized_hook: Union[AsyncIterator[None], Iterator[None]]
    is_async: bool


class ExtensionContextManagerBase:
    __slots__ = ("hook_name", "hooks", "deprecation_message", "default_hook")

    def __init__(
        self,
        hook_name: str,
        extensions: List[Extension],
        execution_context: ExecutionContext,
    ):
        self.hook_name = hook_name
        self.hooks: List[WrappedHook] = []
        self.default_hook: Hook = getattr(Extension, self.hook_name)
        for extension in extensions:
            hook = self.get_hook(extension, execution_context)
            if hook:
                self.hooks.append(hook)

    def get_hook(
        self, extension: Extension, execution_context: ExecutionContext
    ) -> Optional[WrappedHook]:
        hook_fn: Optional[Hook] = getattr(type(extension), self.hook_name)
        hook_fn = hook_fn if hook_fn is not self.default_hook else None

        if hook_fn:
            if inspect.isgeneratorfunction(hook_fn):
                return WrappedHook(
                    extension, hook_fn(extension, execution_context), False
                )

            if inspect.isasyncgenfunction(hook_fn):
                return WrappedHook(
                    extension, hook_fn(extension, execution_context), True
                )

            if callable(hook_fn):
                return self.from_callable(extension, hook_fn, execution_context)

            raise ValueError(
                f"Hook {self.hook_name} on {extension} "
                f"must be callable, received {hook_fn!r}"
            )

        return None

    @staticmethod
    def from_callable(
        extension: Extension,
        func: Hook,
        execution_context: ExecutionContext,
    ) -> WrappedHook:
        if iscoroutinefunction(func):

            async def async_iterator():  # type: ignore[no-untyped-def]
                await func(extension, execution_context)
                yield

            hook = async_iterator()
            return WrappedHook(extension, hook, True)
        else:

            def iterator():  # type: ignore[no-untyped-def]
                func(extension, execution_context)
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
