from unittest.mock import patch

import pytest

from graphql import parse

from hiku.schema import Schema
from hiku.types import String
from hiku.executors.sync import SyncExecutor
from hiku.engine import Engine
from hiku.graph import Field, Root, Graph
from hiku.extensions.query_parse_cache import QueryParserCache


@pytest.fixture(name="sync_graph")
def sync_graph_fixture():
    def question(fields):
        return ["Number?" for _ in fields]

    def answer(fields):
        return ["42" for _ in fields]

    return Graph([Root([
        Field("question", String, question),
        Field("answer", String, answer),
    ])])


def test_query_parser_cache_extension(sync_graph):
    schema = Schema(
        Engine(SyncExecutor()), sync_graph,
        extensions=[QueryParserCache(2)],
    )

    with patch("hiku.readers.graphql.parse", wraps=parse) as mock_parse:
        result = schema.execute_sync("{answer}")
        assert result.data == {"answer": "42"}

        assert mock_parse.call_count == 1

        for _ in range(3):
            result = schema.execute_sync("{answer}")
            assert result.data == {"answer": "42"}

        # check that parse was called only once
        assert mock_parse.call_count == 1

        # check that new query was parsed
        result = schema.execute_sync("{question}")
        assert result.data == {"question": "Number?"}

        assert mock_parse.call_count == 2
