from unittest.mock import patch

import pytest

from hiku.schema import Schema
from hiku.validate.query import validate
from hiku.extensions.query_validation_cache import QueryValidationCache
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


def test_query_validation_cache_extension(sync_graph):
    schema = Schema(
        Engine(SyncExecutor()), sync_graph,
        extensions=[QueryValidationCache(2)],
    )

    with patch("hiku.schema.validate", wraps=validate) as mock_validate:
        result = schema.execute_sync("{answer}")
        assert result.data == {"answer": "42"}

        assert mock_validate.call_count == 1

        for _ in range(3):
            result = schema.execute_sync("{answer}")
            assert result.data == {"answer": "42"}

        # check that read_operation was called only once
        assert mock_validate.call_count == 1

        # check that new query was parsed
        result = schema.execute_sync("{question}")
        assert result.data == {"question": "Number?"}

        assert mock_validate.call_count == 2
