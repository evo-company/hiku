from functools import lru_cache
from typing import Iterator, Optional

from hiku.context import ExecutionContext
from hiku.extensions.base_extension import Extension
from hiku.readers.graphql import read_operation
from hiku.utils import to_immutable_dict


class QueryTransformCache(Extension):
    """Sets up lru cache for the ast to Node transformation.

    :param int maxsize: Maximum size of the cache
    """

    def __init__(self, maxsize: Optional[int] = None):
        self.cached_operation_reader = lru_cache(maxsize=maxsize)(
            read_operation
        )

    def on_operation(
        self, execution_context: ExecutionContext
    ) -> Iterator[None]:
        execution_context.operation = self.cached_operation_reader(
            execution_context.graphql_document,
            to_immutable_dict(execution_context.variables)
            if execution_context.variables
            else None,
            execution_context.request_operation_name,
        )

        yield
