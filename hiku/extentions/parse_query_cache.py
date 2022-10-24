from functools import lru_cache
from typing import (
    Callable,
    Any,
)

from graphql.language import ast

from hiku.extentions import Extension
from hiku.readers.graphql import parse_query
from hiku.telemetry.prometheus import (
    QUERY_CACHE_HITS,
    QUERY_CACHE_MISSES,
)


def wrap_metrics(cached_parser: Callable) -> Callable:
    def wrapper(*args: Any, **kwargs: Any) -> ast.DocumentNode:
        document = cached_parser(*args, **kwargs)
        info = cached_parser.cache_info()  # type: ignore
        QUERY_CACHE_HITS.set(info.hits)
        QUERY_CACHE_MISSES.set(info.misses)
        return document
    return wrapper


class ParseQueryCache(Extension):
    def __init__(self, max_size: int) -> None:
        super().__init__()
        self._parse = wrap_metrics(lru_cache(maxsize=max_size)(parse_query))

    def on_parsing_start(self):
        self.execution_context.graphql_document = self._parse(
            self.execution_context.query
        )
