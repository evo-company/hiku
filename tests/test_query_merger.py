import pytest
from graphql import print_ast
from graphql.language.parser import parse

from hiku.export.graphql import export
from hiku.graph import Field, Graph, Interface, Link, Node, Option, Root, Union
from hiku.merge import QueryMerger
from hiku.readers.graphql import read
from hiku.types import (
    Boolean,
    Integer,
    InterfaceRef,
    Optional,
    Sequence,
    String,
    TypeRef,
    UnionRef,
)


def mock_resolve(): ...


GRAPH = Graph(
    [
        Node(
            "User",
            [
                Field("id", String, mock_resolve),
                Field(
                    "name",
                    String,
                    mock_resolve,
                    options=[Option("capitalize", Optional[Boolean], default=False)],
                ),
                Link("info", TypeRef["Info"], mock_resolve, requires=None),
                Link(
                    "playlist",
                    Sequence[InterfaceRef["Media"]],
                    mock_resolve,
                    requires=None,
                ),
            ],
        ),
        Node(
            "Info",
            [
                Field("email", String, mock_resolve),
                Field("phone", String, mock_resolve),
                Link(
                    "transport",
                    Optional[UnionRef["Transport"]],
                    mock_resolve,
                    requires=None,
                ),
            ],
        ),
        Node(
            "Context",
            [Link("user", TypeRef["User"], mock_resolve, requires=None)],
        ),
        Node(
            "Audio",
            [
                Field("format", String, mock_resolve),
            ],
            implements=["Media"],
        ),
        Node(
            "Video",
            [
                Field("codec", String, mock_resolve),
            ],
            implements=["Media"],
        ),
        Node(
            "Car",
            [
                Field("model", String, mock_resolve),
                Field("year", String, mock_resolve),
            ],
        ),
        Node(
            "Bike",
            [
                Field("model", String, mock_resolve),
            ],
        ),
        Root([Link("context", TypeRef["Context"], mock_resolve, requires=None)]),
    ],
    interfaces=[
        Interface(
            "Media",
            [Field("duration", Integer, mock_resolve)],
        )
    ],
    unions=[Union("Transport", ["Car", "Bike"])],
)


@pytest.mark.parametrize(
    "src,result",
    [
        pytest.param(
            """
        query TestQuery {
            context {
                user {
                    id
                    name
                    capName: name(capitalize: true)
                    info {
                        email
                        phone
                        transport {
                            ... on Car { model year }
                            ... on Bike { model }
                        }
                    }
                    playlist {
                        ... on Audio { duration format }
                        ... on Video { duration codec }
                    }
                }
            }
        }
        """,
            """
        {
            context {
                user {
                    id
                    name
                    capName: name(capitalize: true)
                    info {
                        email
                        phone
                        transport {
                            ... on Car { model year }
                            ... on Bike { model }
                        }
                    }
                    playlist {
                        duration
                        ... on Audio { format }
                        ... on Video { codec }
                    }
                }
            }
        }
        """,
            id="full query",
        ),
        pytest.param(
            """
        query TestQuery {
            context { ...ContextFragment }
        }
        fragment ContextFragment on Context {
            ...ContextFragmentA
            ...ContextFragmentB
        }
        fragment ContextFragmentA on Context {
            user { id name }
        }
        fragment ContextFragmentB on Context {
            user { id }
        }
        """,
            """
        { context { user { id name } } }
        """,
            id="only nested fragments",
        ),
        pytest.param(
            """
        query TestQuery {
            context { user { id info { email } } ...ContextFragment }
        }
        fragment ContextFragment on Context {
            ...ContextFragmentA
            ...ContextFragmentB
        }
        fragment ContextFragmentA on Context {
            user { id name }
        }
        fragment ContextFragmentB on Context {
            user { id info { phone } }
        }
        """,
            """
        { context { user { id name info { email phone } } } }
        """,
            id="fields + fragments",
        ),
        pytest.param(
            """
        query TestQuery {
            context { user { id } ...ContextFragment }
        }
        fragment ContextFragment on Context {
            ...ContextFragmentA
            ...ContextFragmentB
        }
        fragment ContextFragmentA on Context {
            user { id name }
        }
        fragment ContextFragmentB on Context {
            user { id capName: name(capitalize: true) }
        }
        """,
            """
        { context { user { id name capName: name(capitalize: true) } } }
        """,
            id="fields + aliases + fragments",
        ),
    ],
)
def test_query_merger(src, result):
    exp = print_ast(parse(result)).strip()

    query = QueryMerger(GRAPH).merge(read(src))
    got = print_ast(export(query)).strip()

    assert got == exp


@pytest.mark.parametrize(
    "src,result",
    [
        pytest.param(
            """
        query PlaylistUpdateQuery {
            playlistGuide {
                lastUpdate {
                    __typename
                    ...PlaylistUpdate
                }
            }
        }

        fragment PlaylistContextFragment on PlaylistContext {
            artistId
            albumId
        }

        fragment PlaylistActionFragment on PlaylistAction {
            __typename
            ... on PlayTrackAction {
                id
                title
            }
            ... on ChooseTrackAction {
                id
                title
            }
        }

        fragment PlaylistEntryFragment on PlaylistEntry {
            __typename
            actions {
                __typename
                ...PlaylistActionFragment
            }
        }

        fragment PlaylistUpdate on PlaylistUpdate {
            __typename
            ... on ChooseTracksUpdate {
                node {
                    ...PlaylistEntryFragment
                }
            }
            ... on ContactCuratorUpdate {
                context {
                    ...PlaylistContextFragment
                }
                node {
                    ...PlaylistEntryFragment
                }
            }
        }
        """,
            """
        {
            playlistGuide {
                lastUpdate {
                    __typename
                    ... on ChooseTracksUpdate {
                        node {
                            __typename
                            actions {
                                __typename
                                ... on PlayTrackAction {
                                    id
                                    title
                                }
                                ... on ChooseTrackAction {
                                    id
                                    title
                                }
                            }
                        }
                    }
                    ... on ContactCuratorUpdate {
                        context {
                            artistId
                            albumId
                        }
                        node {
                            __typename
                            actions {
                                __typename
                                ... on PlayTrackAction {
                                    id
                                    title
                                }
                                ... on ChooseTrackAction {
                                    id
                                    title
                                }
                            }
                        }
                    }
                }
            }
        }
        """,
            id="original-style playlist query normalizes wrapper fragments",
        ),
        pytest.param(
            """
        query PlaylistUpdateQuery__router__0 {
            playlistGuide {
                lastUpdate {
                    __typename
                    ... on ChooseTracksUpdate {
                        node {
                            ...l
                        }
                    }
                    ... on ContactCuratorUpdate {
                        context {
                            ...b
                        }
                        node {
                            ...l
                        }
                    }
                }
            }
        }

        fragment b on PlaylistContext {
            artistId
            albumId
        }

        fragment c on PlayTrackAction {
            id
            title
        }

        fragment d on ChooseTrackAction {
            id
            title
        }

        fragment k on PlaylistAction {
            __typename
            ...c
            ...d
        }

        fragment l on PlaylistEntry {
            __typename
            actions {
                ...k
            }
        }
        """,
            """
        {
            playlistGuide {
                lastUpdate {
                    __typename
                    ... on ChooseTracksUpdate {
                        node {
                            __typename
                            actions {
                                __typename
                                ...c
                                ...d
                            }
                        }
                    }
                    ... on ContactCuratorUpdate {
                        context {
                            artistId
                            albumId
                        }
                        node {
                            __typename
                            actions {
                                __typename
                                ...c
                                ...d
                            }
                        }
                    }
                }
            }
        }

        fragment c on PlayTrackAction {
            id
            title
        }

        fragment d on ChooseTrackAction {
            id
            title
        }
        """,
            id="apollo-router-style playlist query normalizes wrapper fragments",
        ),
        pytest.param(
            """
        query PlaylistUpdateQuery__router__1 {
            playlistGuide {
                lastUpdate {
                    __typename
                    ... on ContactCuratorUpdate {
                        context {
                            ...b
                        }
                        node {
                            ...l
                        }
                    }
                }
            }
        }

        fragment b on PlaylistContext {
            artistId
            albumId
        }

        fragment c on PlayTrackAction {
            id
            title
        }

        fragment d on ChooseTrackAction {
            id
            title
        }

        fragment k on PlaylistAction {
            __typename
            ...c
            ...d
        }

        fragment l on PlaylistEntry {
            __typename
            actions {
                ...k
            }
        }
        """,
            """
        {
            playlistGuide {
                lastUpdate {
                    __typename
                    ... on ContactCuratorUpdate {
                        context {
                            artistId
                            albumId
                        }
                        node {
                            __typename
                            actions {
                                __typename
                                ...c
                                ...d
                            }
                        }
                    }
                }
            }
        }

        fragment c on PlayTrackAction {
            id
            title
        }

        fragment d on ChooseTrackAction {
            id
            title
        }
        """,
            id="apollo-router-style playlist query without choosetracks still normalizes wrapper fragments",
        ),
    ],
)
def test_query_merger_my(src, result):
    exp = print_ast(parse(result)).strip()

    graph = Graph(
        [
            Node(
                "PlayTrackAction",
                [
                    Field("id", Integer, mock_resolve),
                    Field("title", String, mock_resolve),
                ],
            ),
            Node(
                "ChooseTrackAction",
                [
                    Field("id", Integer, mock_resolve),
                    Field("title", String, mock_resolve),
                ],
            ),
            Node(
                "PlaylistEntry",
                [
                    Field("__typename", String, mock_resolve),
                    Link(
                        "actions",
                        Sequence[UnionRef["PlaylistAction"]],
                        mock_resolve,
                        requires=None,
                    ),
                ],
            ),
            Node(
                "PlaylistContext",
                [
                    Field("artistId", String, mock_resolve),
                    Field("albumId", String, mock_resolve),
                ],
            ),
            Node(
                "ChooseTracksUpdate",
                [
                    Field("__typename", String, mock_resolve),
                    Link(
                        "node",
                        TypeRef["PlaylistEntry"],
                        mock_resolve,
                        requires=None,
                    ),
                ],
            ),
            Node(
                "ContactCuratorUpdate",
                [
                    Field("__typename", String, mock_resolve),
                    Link(
                        "context",
                        TypeRef["PlaylistContext"],
                        mock_resolve,
                        requires=None,
                    ),
                    Link(
                        "node",
                        TypeRef["PlaylistEntry"],
                        mock_resolve,
                        requires=None,
                    ),
                ],
            ),
            Node(
                "PlaylistGuide",
                [
                    Link(
                        "lastUpdate",
                        UnionRef["PlaylistUpdate"],
                        mock_resolve,
                        requires=None,
                    ),
                ],
            ),
            Root(
                [
                    Link(
                        "playlistGuide",
                        TypeRef["PlaylistGuide"],
                        mock_resolve,
                        requires=None,
                    ),
                ]
            ),
        ],
        unions=[
            Union(
                "PlaylistAction",
                [
                    "PlayTrackAction",
                    "ChooseTrackAction",
                ],
            ),
            Union(
                "PlaylistUpdate",
                ["ChooseTracksUpdate", "ContactCuratorUpdate"],
            ),
        ],
    )

    query = QueryMerger(graph).merge(read(src))
    got = print_ast(export(query)).strip()

    assert got == exp


@pytest.mark.parametrize(
    "src,result",
    [
        pytest.param(
            """
        query TestQuery {
            context { user { info { transport {
                ... on Car { year }
                ...TransportFragment
            } } } }
        }
        fragment TransportFragment on Transport {
            ... on Car { year }
            ... on Car { model }
            ... on Bike { model }
        }
        """,
            """
        { context { user { info { transport {
            ... on Car { year model }
            ... on Bike { model }
        } } } } }
        """,
            id="union fragments inside fragment",
        ),
        pytest.param(
            """
        query TestQuery { context { user { info { transport {
            ... on Car { year }
            ... on Car { model }
            ... on Bike { model }
        } } } } }
        """,
            """
        { context { user { info { transport {
            ... on Car { year model }
            ... on Bike { model }
        } } } } }
        """,
            id="union fragments flat",
        ),
    ],
)
def test_query_merger__unions(src, result):
    exp = print_ast(parse(result)).strip()
    query = read(src)
    query = QueryMerger(GRAPH).merge(query)
    got = print_ast(export(query)).strip()

    assert got == exp


@pytest.mark.parametrize(
    "src,result",
    [
        pytest.param(
            """
        query TestQuery { context { user { playlist {
            ... on Audio { duration format }
            ... on Video { duration codec }
        } } } }
        """,
            """
        { context { user { playlist {
            duration
            ... on Audio { format }
            ... on Video { codec }
        } } } }
        """,
            id="interface fragments - fields inside fragments",
        ),
        pytest.param(
            """
        query TestQuery { context { user { playlist {
            duration
            ... on Audio { format }
            ... on Video { duration codec }
        } } } }
        """,
            """
        { context { user { playlist {
            duration
            ... on Audio { format }
            ... on Video { codec }
        } } } }
        """,
            id="interface fragments - fields inside and outside fragments",
        ),
        pytest.param(
            """
        query TestQuery { context { user { playlist {
            ...PlaylistFragment
        } } } }
        fragment PlaylistFragment on Media {
            ... on Audio { duration format }
            ... on Video { duration codec }
        }
        """,
            """
        { context { user { playlist {
            duration
            ... on Audio { format }
            ... on Video { codec }
        } } } }
        """,
            id="interface fragments - fragments inside fragments",
        ),
    ],
)
def test_query_merger__interfaces(src, result):
    exp = print_ast(parse(result)).strip()

    query = QueryMerger(GRAPH).merge(read(src))
    got = print_ast(export(query)).strip()

    assert got == exp


def test_query_merger__non_existing_link():
    src = """
    query TestQuery {
        nonExistingLink { id }
    }
    """
    with pytest.raises(KeyError) as e:
        QueryMerger(GRAPH).merge(read(src))

    assert e.value is not None
