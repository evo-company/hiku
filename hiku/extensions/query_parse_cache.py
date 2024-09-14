from functools import lru_cache
from typing import Iterator, Optional

from prometheus_client import Gauge

from hiku.context import ExecutionContext
from hiku.extensions.base_extension import Extension
from hiku.readers.graphql import parse_query

QUERY_CACHE_HITS = Gauge("hiku_query_cache_hits", "Query cache hits")
QUERY_CACHE_MISSES = Gauge("hiku_query_cache_misses", "Query cache misses")


class QueryParserCache(Extension):
    """Sets up lru cache for the ast parsing.

    Exposes two metrics:
    - hiku_query_cache_hits
    - hiku_query_cache_misses

    :param int maxsize: Maximum size of the cache
    """

    def __init__(self, maxsize: Optional[int] = None):
        self.cached_parser = lru_cache(maxsize=maxsize)(parse_query)

    def on_parse(self, execution_context: ExecutionContext) -> Iterator[None]:
        if execution_context.query_src:
            execution_context.graphql_document = self.cached_parser(
                execution_context.query_src,
            )

            info = self.cached_parser.cache_info()
            QUERY_CACHE_HITS.set(info.hits)
            QUERY_CACHE_MISSES.set(info.misses)
        yield
