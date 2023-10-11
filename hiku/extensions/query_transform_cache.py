from functools import lru_cache
from typing import Callable, Iterator, Optional

from hiku.utils import to_immutable_dict

from hiku.extensions.base_extension import Extension, ExtensionFactory
from hiku.readers.graphql import read_operation


class _QueryTransformCacheImpl(Extension):
    """Sets up lru cache for the ast to Node transformation.

    :param int maxsize: Maximum size of the cache
    """

    def __init__(self, cached_operation_reader: Callable):
        self.cached_operation_reader = cached_operation_reader

    def on_operation(self) -> Iterator[None]:
        execution_context = self.execution_context

        execution_context.operation = self.cached_operation_reader(
            execution_context.graphql_document,
            to_immutable_dict(execution_context.variables)
            if execution_context.variables
            else None,
            execution_context.request_operation_name,
        )

        yield


class QueryTransformCache(ExtensionFactory):
    ext_class = _QueryTransformCacheImpl

    def __init__(self, maxsize: Optional[int] = None):
        self.cached_operation_reader = lru_cache(maxsize=maxsize)(
            read_operation
        )
        super().__init__(self.cached_operation_reader)
