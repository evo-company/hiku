from unittest.mock import Mock

import pytest

from hiku.executors.asyncio import AsyncIOExecutor
from hiku.executors.sync import SyncExecutor
from hiku.federation.directive import External, Key, Requires
from hiku.federation.graph import FederatedNode, Graph
from hiku.federation.schema import Schema
from hiku.graph import Field, Link, Node, Root, Union
from hiku.types import Integer, Optional, Sequence, String, TypeRef

from tests.test_federation.utils import (
    GRAPH,
    ASYNC_GRAPH,
    async_direct_link,
    direct_link,
    id_resolver,
    resolve_reference_direct,
)


def execute_schema_v1(query):
    return Schema(
        SyncExecutor(),
        GRAPH,
        federation_version=1,
    ).execute_sync(query["query"], query["variables"], query["operationName"])


def execute_schema_v2(query):
    return Schema(
        SyncExecutor(),
        GRAPH,
    ).execute_sync(query["query"], query["variables"], query["operationName"])


async def execute_async_schema_v1(query):
    return await Schema(
        AsyncIOExecutor(),
        ASYNC_GRAPH,
        federation_version=1,
    ).execute(query["query"], query["variables"], query["operationName"])


async def execute_async_schema_v2(query):
    return await Schema(
        AsyncIOExecutor(),
        ASYNC_GRAPH,
    ).execute(query["query"], query["variables"], query["operationName"])


ENTITIES_QUERY = {
    "query": """
        query RepresentationsQuery($representations:[_Any!]!) {
            _entities(representations:$representations) {
                ...on Cart {
                    status { id title }
                }
            }
        }
        """,
    "variables": {
        "representations": [
            {"__typename": "Cart", "id": 1},
            {"__typename": "Cart", "id": 2},
        ]
    },
    "operationName": "RepresentationsQuery",
}

SDL_QUERY = {
    "query": "query __ApolloGetServiceDefinition__ { _service { sdl } }",
    "variables": None,
    "operationName": "__ApolloGetServiceDefinition__",
}


@pytest.mark.parametrize("execute", [execute_schema_v1, execute_schema_v2])
def test_fetch_sdl(execute):
    result = execute(SDL_QUERY)
    assert result.data["_service"]["sdl"] is not None


@pytest.mark.parametrize(
    "execute", [execute_async_schema_v1, execute_async_schema_v2]
)
@pytest.mark.asyncio
async def test_fetch_sdl_async(execute):
    result = await execute(SDL_QUERY)
    assert result.data["_service"]["sdl"] is not None


@pytest.mark.parametrize("execute", [execute_schema_v1, execute_schema_v2])
def test_execute_sync(execute):
    result = execute(ENTITIES_QUERY)

    expect = [
        {"status": {"id": "NEW", "title": "new"}},
        {"status": {"id": "ORDERED", "title": "ordered"}},
    ]
    assert expect == result.data["_entities"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "execute", [execute_async_schema_v1, execute_async_schema_v2]
)
async def test_execute_async(execute):
    result = await execute(ENTITIES_QUERY)

    expect = [
        {"status": {"id": "NEW", "title": "new"}},
        {"status": {"id": "ORDERED", "title": "ordered"}},
    ]
    assert expect == result.data["_entities"]


def test_multiple_types_in_representations():
    resolve_author_by_audio_id = Mock(side_effect=direct_link)
    resolve_author_by_id = Mock(side_effect=direct_link)
    resolve_reference_direct_audio = Mock(side_effect=resolve_reference_direct)
    resolve_reference_direct_video = Mock(side_effect=resolve_reference_direct)

    def fields_reference_resolver(
        fields: list[Field], representations: list[dict]
    ) -> list[list]:
        return [[r[f.name] for f in fields] for r in representations]

    graph = Graph(
        [
            Node(
                "Author",
                [
                    Field("id", Integer, id_resolver),
                ],
            ),
            FederatedNode(
                "Audio",
                [
                    Field("id", Integer, fields_reference_resolver),
                    Link(
                        "author",
                        Optional[TypeRef["Author"]],
                        resolve_author_by_audio_id,
                        requires="id",
                    ),
                ],
                directives=[Key("id")],
                resolve_reference=resolve_reference_direct_audio,
            ),
            FederatedNode(
                "Video",
                [
                    Field("id", Integer, fields_reference_resolver),
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
                        Optional[TypeRef["Author"]],
                        resolve_author_by_id,
                        requires="author_id",
                        directives=[Requires("author_id")],
                    ),
                ],
                directives=[Key("id")],
                resolve_reference=resolve_reference_direct_video,
            ),
            Root([]),
        ],
        unions=[
            Union("Media", ["Audio", "Video"]),
        ],
    )

    schema = Schema(SyncExecutor(), graph)
    query = {
        "query": """
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
        "variables": {
            "representations": [
                {"__typename": "Video", "id": 2, "author_id": 200},
                {"__typename": "Audio", "id": 1},
            ]
        },
        "operationName": "RepresentationsQuery",
    }
    result = schema.execute_sync(
        query["query"], query["variables"], query["operationName"]
    )

    expect = [
        {"__typename": "Video", "id": 2, "author": {"id": 200}},
        {"__typename": "Audio", "id": 1, "author": {"id": 1}},
    ]

    assert expect == result.data["_entities"]

    resolve_author_by_audio_id.assert_called_once_with([1])
    resolve_author_by_id.assert_called_once_with([200])

    resolve_reference_direct_audio.assert_called_once_with(
        [
            {"__typename": "Audio", "id": 1},
        ]
    )

    resolve_reference_direct_video.assert_called_once_with(
        [
            {"__typename": "Video", "id": 2, "author_id": 200},
        ]
    )


@pytest.mark.asyncio
async def test_multiple_types_in_representations_async():
    resolve_author_by_audio_id = Mock(side_effect=direct_link)
    resolve_author_by_id = Mock(side_effect=async_direct_link)
    resolve_reference_direct_audio = Mock(side_effect=resolve_reference_direct)
    resolve_reference_direct_video = Mock(side_effect=resolve_reference_direct)

    def fields_reference_resolver(
        fields: list[Field], representations: list[dict]
    ) -> list[list]:
        return [[r[f.name] for f in fields] for r in representations]

    graph = Graph(
        [
            Node(
                "Author",
                [
                    Field("id", Integer, id_resolver),
                ],
            ),
            FederatedNode(
                "Audio",
                [
                    Field("id", Integer, fields_reference_resolver),
                    Link(
                        "author",
                        Optional[TypeRef["Author"]],
                        resolve_author_by_audio_id,
                        requires="id",
                    ),
                ],
                directives=[Key("id")],
                resolve_reference=resolve_reference_direct_audio,
            ),
            FederatedNode(
                "Video",
                [
                    Field("id", Integer, fields_reference_resolver),
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
                        Optional[TypeRef["Author"]],
                        resolve_author_by_id,
                        requires="author_id",
                        directives=[Requires("author_id")],
                    ),
                ],
                directives=[Key("id")],
                resolve_reference=resolve_reference_direct_video,
            ),
            Root([]),
        ],
        unions=[Union("Media", ["Audio", "Video"])],
        is_async=True,
    )

    schema = Schema(AsyncIOExecutor(), graph)
    query = {
        "query": """
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
        "variables": {
            "representations": [
                {"__typename": "Video", "id": 2, "author_id": 200},
                {"__typename": "Audio", "id": 1},
            ]
        },
        "operationName": "RepresentationsQuery",
    }
    result = await schema.execute(
        query["query"], query["variables"], query["operationName"]
    )

    expect = [
        {"__typename": "Video", "id": 2, "author": {"id": 200}},
        {"__typename": "Audio", "id": 1, "author": {"id": 1}},
    ]

    assert expect == result.data["_entities"]

    resolve_author_by_audio_id.assert_called_once_with([1])
    resolve_author_by_id.assert_called_once_with([200])

    resolve_reference_direct_audio.assert_called_once_with(
        [
            {"__typename": "Audio", "id": 1},
        ]
    )

    resolve_reference_direct_video.assert_called_once_with(
        [
            {"__typename": "Video", "id": 2, "author_id": 200},
        ]
    )


def test_federated_node_link_requires_validation_error():
    """Graph() raises ValueError when a Link's @requires misses transitive fields."""

    def field_resolver(fields, ids): ...
    def link_resolver(reqs): ...

    with pytest.raises(ValueError, match="fieldA"):
        Graph(
            [
                Node("Other", [Field("id", Integer, field_resolver)]),
                FederatedNode(
                    "Entity",
                    [
                        Field("id", Integer, field_resolver),
                        Field(
                            "fieldA",
                            Optional[Integer],
                            field_resolver,
                            directives=[External()],
                        ),
                        Field(
                            "fieldB",
                            Optional[Integer],
                            field_resolver,
                            directives=[Requires("fieldA")],
                        ),
                        Field(
                            "fieldC",
                            Optional[Integer],
                            field_resolver,
                            directives=[External()],
                        ),
                        Link(
                            "items",
                            Sequence[TypeRef["Other"]],
                            link_resolver,
                            requires=["fieldC", "fieldB"],
                            directives=[
                                Requires("fieldC")
                            ],  # missing fieldA → error
                        ),
                    ],
                    directives=[Key("id")],
                    resolve_reference=lambda reps: reps,
                ),
                Root([]),
            ]
        )


def test_federated_node_link_requires_validation_error_single_requires():
    """Graph() raises ValueError when a Link's single string requires misses transitive fields."""

    def field_resolver(fields, ids): ...
    def link_resolver(reqs): ...

    with pytest.raises(ValueError, match="fieldA"):
        Graph(
            [
                Node("Other", [Field("id", Integer, field_resolver)]),
                FederatedNode(
                    "Entity",
                    [
                        Field("id", Integer, field_resolver),
                        Field(
                            "fieldA",
                            Optional[Integer],
                            field_resolver,
                            directives=[External()],
                        ),
                        Field(
                            "fieldB",
                            Optional[Integer],
                            field_resolver,
                            directives=[Requires("fieldA")],
                        ),
                        Link(
                            "items",
                            Sequence[TypeRef["Other"]],
                            link_resolver,
                            requires="fieldB",  # single string, not list
                            directives=[Requires("fieldB")],  # missing fieldA → error
                        ),
                    ],
                    directives=[Key("id")],
                    resolve_reference=lambda reps: reps,
                ),
                Root([]),
            ]
        )


def test_federated_node_link_requires_no_error_when_complete():
    """Graph() succeeds when Link's @requires covers all transitive fields."""

    def field_resolver(fields, ids): ...
    def link_resolver(reqs): ...

    # Should not raise — directive declares both fieldA and fieldB
    Graph(
        [
            Node("Other", [Field("id", Integer, field_resolver)]),
            FederatedNode(
                "Entity",
                [
                    Field("id", Integer, field_resolver),
                    Field(
                        "fieldA",
                        Optional[Integer],
                        field_resolver,
                        directives=[External()],
                    ),
                    Field(
                        "fieldB",
                        Optional[Integer],
                        field_resolver,
                        directives=[Requires("fieldA")],
                    ),
                    Field(
                        "fieldC",
                        Optional[Integer],
                        field_resolver,
                        directives=[External()],
                    ),
                    Link(
                        "items",
                        Sequence[TypeRef["Other"]],
                        link_resolver,
                        requires=["fieldC", "fieldB"],
                        directives=[Requires("fieldA fieldC")],
                    ),
                ],
                directives=[Key("id")],
                resolve_reference=lambda reps: reps,
            ),
            Root([]),
        ]
    )


def test_federated_node_link_no_requires_unaffected():
    """Graph() is unaffected for Links with requires=None."""

    def field_resolver(fields, ids): ...
    def link_resolver(opts): ...

    # Should not raise — Link has no requires at all
    Graph(
        [
            FederatedNode(
                "SomeEntity",
                [
                    Field("id", Integer, field_resolver),
                    Link(
                        "related",
                        Sequence[TypeRef["SomeEntity"]],
                        link_resolver,
                        requires=None,
                    ),
                ],
                directives=[Key("id")],
                resolve_reference=lambda reps: reps,
            ),
            Root([]),
        ]
    )


def test_regular_node_link_not_validated():
    """Regular (non-federated) nodes are not validated."""

    def field_resolver(fields, ids): ...
    def link_resolver(reqs): ...

    # categoryId has @requires but Link's @requires only covers vehicleId.
    # This should NOT raise because it's a regular Node, not a FederatedNode.
    Graph(
        [
            Node(
                "RegularNode",
                [
                    Field(
                        "productId",
                        Optional[Integer],
                        field_resolver,
                        directives=[External()],
                    ),
                    Field(
                        "categoryId",
                        Optional[Integer],
                        field_resolver,
                        directives=[Requires("productId")],
                    ),
                    Field(
                        "vehicleId",
                        Optional[Integer],
                        field_resolver,
                        directives=[External()],
                    ),
                    Link(
                        "userVehicles",
                        Sequence[TypeRef["RegularNode"]],
                        link_resolver,
                        requires=["vehicleId", "categoryId"],
                        directives=[Requires("vehicleId")],
                    ),
                ],
            ),
            Root([]),
        ]
    )
