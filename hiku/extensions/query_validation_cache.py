from functools import lru_cache
from typing import Iterator, Optional

from hiku.endpoint.graphql import _run_validation
from hiku.extensions.base_extension import Extension


class QueryValidationCache(Extension):
    """Sets up lru cache for the query Node validation.

    :param int maxsize: Maximum size of the cache
    """

    def __init__(self, maxsize: Optional[int] = None):
        self.cached_validator = lru_cache(maxsize=maxsize)(_run_validation)

    def on_validate(self) -> Iterator[None]:
        execution_context = self.execution_context

        execution_context.errors = self.cached_validator(
            execution_context.graph,
            execution_context.query,
            execution_context.validators,
        )

        yield
