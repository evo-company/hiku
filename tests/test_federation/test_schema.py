from unittest.mock import Mock

import pytest

from hiku.executors.asyncio import AsyncIOExecutor
from hiku.executors.sync import SyncExecutor
from hiku.federation.directive import External, Key, Requires
from hiku.federation.graph import FederatedNode, Graph
from hiku.federation.schema import Schema
from hiku.graph import Field, Link, Node, Root, Union
from hiku.types import Integer, Optional, String, TypeRef
from hiku.utils import to_immutable_dict

from tests.test_federation.utils import (
    GRAPH,
    ASYNC_GRAPH, id_resolver,
)


def execute_schema_v1(query):
    return Schema(
        SyncExecutor(),
        GRAPH,
        federation_version=1,
    ).execute_sync(query['query'], query['variables'], query['operationName'])


def execute_schema_v2(query):
    return Schema(
        SyncExecutor(),
        GRAPH,
    ).execute_sync(query['query'], query['variables'], query['operationName'])


async def execute_async_schema_v1(query):
    return await Schema(
        AsyncIOExecutor(),
        ASYNC_GRAPH,
        federation_version=1,
    ).execute(query['query'], query['variables'], query['operationName'])


async def execute_async_schema_v2(query):
    return await Schema(
        AsyncIOExecutor(),
        ASYNC_GRAPH,
    ).execute(query['query'], query['variables'], query['operationName'])


ENTITIES_QUERY = {
    'query': """
        query RepresentationsQuery($representations:[_Any!]!) {
            _entities(representations:$representations) {
                ...on Cart {
                    status { id title }
                }
            }
        }
        """,
    'variables': {
        'representations': [
            {'__typename': 'Cart', 'id': 1},
            {'__typename': 'Cart', 'id': 2},
        ]
    },
    'operationName': 'RepresentationsQuery',
}

SDL_QUERY = {
    'query': "query __ApolloGetServiceDefinition__ { _service { sdl } }",
    'variables': None,
    'operationName': '__ApolloGetServiceDefinition__',
}


@pytest.mark.parametrize('execute', [
    execute_schema_v1,
    execute_schema_v2
])
def test_fetch_sdl(execute):
    result = execute(SDL_QUERY)
    assert result.data['_service']['sdl'] is not None


@pytest.mark.parametrize('execute', [
    execute_async_schema_v1,
    execute_async_schema_v2
])
@pytest.mark.asyncio
async def test_fetch_sdl_async(execute):
    result = await execute(SDL_QUERY)
    assert result.data['_service']['sdl'] is not None


@pytest.mark.parametrize('execute', [
    execute_schema_v1,
    execute_schema_v2
])
def test_execute_sync(execute):
    result = execute(ENTITIES_QUERY)

    expect = [
        {'status': {'id': 'NEW', 'title': 'new'}},
        {'status': {'id': 'ORDERED', 'title': 'ordered'}}
    ]
    assert expect == result.data['_entities']


@pytest.mark.asyncio
@pytest.mark.parametrize('execute', [
    execute_async_schema_v1,
    execute_async_schema_v2
])
async def test_execute_async(execute):
    result = await execute(ENTITIES_QUERY)

    expect = [
        {'status': {'id': 'NEW', 'title': 'new'}},
        {'status': {'id': 'ORDERED', 'title': 'ordered'}}
    ]
    assert expect == result.data['_entities']


def test_multiple_types_in_representations():
    def resolve_reference_direct(representations: list[dict]):
        return [to_immutable_dict(r) for r in representations]

    resolve_author_by_audio_id = Mock(side_effect=lambda ids: ids)
    resolve_author_by_id = Mock(side_effect=lambda ids: ids)
    resolve_reference_direct_audio = Mock(side_effect=resolve_reference_direct)
    resolve_reference_direct_video = Mock(side_effect=resolve_reference_direct)

    def fields_reference_resolver(
        fields: list[Field], representations: list[dict]
    ) -> list[list]:
        return [[r[f.name] for f in fields] for r in representations]

    graph = Graph([
        Node('Author', [
            Field('id', Integer, id_resolver),
        ]),
        FederatedNode('Audio', [
            Field('id', Integer, fields_reference_resolver),
            Link(
                "author",
                Optional[TypeRef['Author']],
                resolve_author_by_audio_id,
                requires="id"
            ),
        ], directives=[Key('id')], resolve_reference=resolve_reference_direct_audio),
        FederatedNode('Video', [
            Field('id', Integer, fields_reference_resolver),
            # Video.author_name is a external field, and should be
            # resolved by the gateway and passed to us in a representations
            Field(
                "author_id",
                String,
                fields_reference_resolver,
                directives=[External()],
            ),
            Link(
                "author",
                Optional[TypeRef['Author']],
                resolve_author_by_id,
                requires="author_id",
                directives=[Requires("author_id")],
            ),
        ], directives=[Key('id')], resolve_reference=resolve_reference_direct_video),
        Root([]),
    ], unions=[Union('Media', ['Audio', 'Video']),])


    schema = Schema(SyncExecutor(), graph)
    query = {
        'query': """
            query RepresentationsQuery($representations:[_Any!]!) {
                _entities(representations:$representations) {
                    __typename
                    ...on Audio {
                        id author { id }
                    }
                    ...on Video {
                        id author { id }
                    }
                }
            }
            """,
        'variables': {
            'representations': [
                {'__typename': 'Video', 'id': 2, "author_id": 200},
                {'__typename': 'Audio', 'id': 1},
            ]
        },
        'operationName': 'RepresentationsQuery',
    }
    result = schema.execute_sync(query['query'], query['variables'], query['operationName'])

    expect = [
        {"__typename": "Video", "id": 2, 'author': {'id': 200}},
        {"__typename": "Audio", "id": 1, 'author': {'id': 1}},
    ]

    assert expect == result.data['_entities']

    resolve_author_by_audio_id.assert_called_once_with([1])
    resolve_author_by_id.assert_called_once_with([200])

    resolve_reference_direct_audio.assert_called_once_with([
        {'__typename': 'Audio', 'id': 1},
    ])

    resolve_reference_direct_video.assert_called_once_with([
        {'__typename': 'Video', 'id': 2, "author_id": 200},
    ])
