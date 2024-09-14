from functools import lru_cache
from typing import Iterator, Optional

from hiku.context import ExecutionContext
from hiku.schema import _run_validation
from hiku.extensions.base_extension import Extension


class QueryValidationCache(Extension):
    """Sets up lru cache for the query Node validation.

    :param int maxsize: Maximum size of the cache
    """

    def __init__(self, maxsize: Optional[int] = None):
        self.cached_validator = lru_cache(maxsize=maxsize)(_run_validation)

    def on_validate(
        self, execution_context: ExecutionContext
    ) -> Iterator[None]:
        execution_context.errors = self.cached_validator(
            execution_context.graph,
            execution_context.query,
            execution_context.validators,
        )

        yield
