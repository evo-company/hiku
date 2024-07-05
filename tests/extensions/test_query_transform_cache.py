from unittest.mock import patch

import pytest

from hiku.readers.graphql import get_operation
from hiku.extensions.query_transform_cache import QueryTransformCache
from hiku.schema import Schema
from hiku.types import String
from hiku.executors.sync import SyncExecutor
from hiku.engine import Engine
from hiku.graph import Field, Root, Graph


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


def test_query_transform_cache_extension(sync_graph):
    schema = Schema(
        Engine(SyncExecutor()), sync_graph,
        extensions=[QueryTransformCache(2)],
    )

    with patch("hiku.readers.graphql.get_operation", wraps=get_operation) as mock_get_operation:
        result = schema.execute_sync({"query": "{answer}"})
        assert result == {"data": {"answer": "42"}}

        assert mock_get_operation.call_count == 1

        for _ in range(3):
            result = schema.execute_sync({"query": "{answer}"})
            assert result == {"data": {"answer": "42"}}

        # check that read_operation was called only once
        assert mock_get_operation.call_count == 1

        # check that new query was parsed
        result = schema.execute_sync({"query": "{question}"})
        assert result == {"data": {"question": "Number?"}}

        assert mock_get_operation.call_count == 2
