from typing import (
    List,
    TYPE_CHECKING,
    Optional,
)

import pytest
from graphql.language import ast

from hiku.directives import (
    QueryDirective,
    get_directive,
    DirectiveMeta,
)
from hiku.extentions import Extension
from hiku.graph import Graph, Root, Field
from hiku.types import (
    String,
)
from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.readers.graphql import (
    SelectionSetVisitMixin,
)
from hiku.endpoint.graphql import GraphQLEndpoint


if TYPE_CHECKING:
    from hiku.readers.graphql import SelectionSetVisitMixin


@pytest.fixture(name='sync_graph')
def sync_graph_fixture():
    def name(fields):
        return ['bill' for _ in fields]
    return Graph([Root([Field('name', String, name)])])


class Upper(QueryDirective):
    meta = DirectiveMeta(
        name='upper',
        locations=['FIELD'],
        description='Converts the field value to upper case',
        args=[],
    )

    def execute(self, value: str) -> str:
        return value.upper()


class UpperDirective(Extension):
    def on_directives(
        self,
        directives: List[ast.DirectiveNode],
        visitor: 'SelectionSetVisitMixin'
    ) -> Optional[QueryDirective]:
        obj = get_directive('upper', directives)
        if obj.name.value != 'upper':
            return None

        if len(obj.arguments):
            raise TypeError('@upper directive does not accept any arguments: {}'
                            .format(len(obj.arguments)))

        return Upper()


def test_directive_works(sync_graph):
    endpoint = GraphQLEndpoint(Engine(SyncExecutor()), sync_graph,
                               extensions=[UpperDirective])
    result = endpoint.dispatch({'query': '{name @upper}'})
    assert result == {'data': {'name': 'BILL'}}
