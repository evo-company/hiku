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
        query QueryMergerMy {
            supportChat {
                history {
                    lastUpdate {
                        __typename
                        ...ChatBotUpdate
                    }
                }
            }
        }

        fragment SimpleContextFragment on SimpleContext {
            maybeCompanyId
            maybeOrderId
        }

        fragment ChatBotActionFragment on ChatBotAction {
            __typename
            ... on SimpleAction {
                id
                title
            }
            ... on ChooseOrderAction {
                id
                title
            }
        }

        fragment ChatBotNodeFragment on ChatNode {
            __typename
            actions {
                __typename
                ...ChatBotActionFragment
            }
        }

        fragment ChatBotUpdate on ChatBotUpdate {
            __typename
            ... on ChooseOrdersUpdate {
                node {
                    ...ChatBotNodeFragment
                }
            }
            ... on ContactOperatorUpdate {
                context {
                    ...SimpleContextFragment
                }
                node {
                    ...ChatBotNodeFragment
                }
            }
        }
        """,
            """
        {
            supportChat {
                history {
                    lastUpdate {
                        __typename
                        ... on ChooseOrdersUpdate {
                            node {
                                ...ChatBotNodeFragment
                            }
                        }
                        ... on ContactOperatorUpdate {
                            context {
                                ...SimpleContextFragment
                            }
                            node {
                                ...ChatBotNodeFragment
                            }
                        }
                    }
                }
            }
        }

        fragment ChatBotNodeFragment on ChatNode {
            __typename
            actions {
                __typename
                ...ChatBotActionFragment
            }
        }

        fragment ChatBotActionFragment on ChatBotAction {
            __typename
            ... on SimpleAction {
                id
                title
            }
            ... on ChooseOrderAction {
                id
                title
            }
        }

        fragment SimpleContextFragment on SimpleContext {
            maybeCompanyId
            maybeOrderId
        }
        """,
            id="original-style reduced production query keeps action fragment",
        ),
        pytest.param(
            """
        query ChatHistoryQuery__uaprom__0(
            $ticketCommentAfterCursor: String! = ""
            $ticketCommentPerPage: Int! = 0
        ) {
            supportChat {
                history {
                    lastUpdate {
                        __typename
                        ... on ChooseOrdersUpdate {
                            node {
                                ...l
                            }
                        }
                        ... on ContactOperatorUpdate {
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
        }

        fragment b on SimpleContext {
            maybeCompanyId
            maybeOrderId
        }

        fragment c on SimpleAction {
            id
            title
        }

        fragment d on ChooseOrderAction {
            id
            title
        }

        fragment k on ChatBotAction {
            __typename
            ...c
            ...d
        }

        fragment l on ChatNode {
            __typename
            actions {
                ...k
            }
        }
        """,
            """
        {
            supportChat {
                history {
                    lastUpdate {
                        __typename
                        ... on ChooseOrdersUpdate {
                            node {
                                ...l
                            }
                        }
                        ... on ContactOperatorUpdate {
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
        }

        fragment l on ChatNode {
            __typename
            actions {
                ...k
            }
        }

        fragment k on ChatBotAction {
            __typename
            ...c
            ...d
        }

        fragment c on SimpleAction {
            id
            title
        }

        fragment d on ChooseOrderAction {
            id
            title
        }

        fragment b on SimpleContext {
            maybeCompanyId
            maybeOrderId
        }
        """,
            id="apollo-router-style reduced production query keeps action fragment",
        ),
    ],
)
def test_query_merger_my(src, result):
    exp = print_ast(parse(result)).strip()

    graph = Graph(
        [
            Node(
                "SimpleAction",
                [
                    Field("id", Integer, mock_resolve),
                    Field("title", String, mock_resolve),
                ],
            ),
            Node(
                "ChooseOrderAction",
                [
                    Field("id", Integer, mock_resolve),
                    Field("title", String, mock_resolve),
                ],
            ),
            Node(
                "ChatNode",
                [
                    Field("__typename", String, mock_resolve),
                    Link(
                        "actions",
                        Sequence[UnionRef["ChatBotAction"]],
                        mock_resolve,
                        requires=None,
                    ),
                ],
            ),
            Node(
                "SimpleContext",
                [
                    Field("maybeCompanyId", String, mock_resolve),
                    Field("maybeOrderId", String, mock_resolve),
                ],
            ),
            Node(
                "ChooseOrdersUpdate",
                [
                    Field("__typename", String, mock_resolve),
                    Link(
                        "node",
                        TypeRef["ChatNode"],
                        mock_resolve,
                        requires=None,
                    ),
                ],
            ),
            Node(
                "ContactOperatorUpdate",
                [
                    Field("__typename", String, mock_resolve),
                    Link(
                        "context",
                        TypeRef["SimpleContext"],
                        mock_resolve,
                        requires=None,
                    ),
                    Link(
                        "node",
                        TypeRef["ChatNode"],
                        mock_resolve,
                        requires=None,
                    ),
                ],
            ),
            Node(
                "ChatHistory",
                [
                    Link(
                        "lastUpdate",
                        UnionRef["ChatBotUpdate"],
                        mock_resolve,
                        requires=None,
                    ),
                ],
            ),
            Node(
                "SupportChat",
                [
                    Link(
                        "history",
                        TypeRef["ChatHistory"],
                        mock_resolve,
                        requires=None,
                    ),
                ],
            ),
            Root(
                [
                    Link(
                        "supportChat",
                        TypeRef["SupportChat"],
                        mock_resolve,
                        requires=None,
                    ),
                ]
            ),
        ],
        unions=[
            Union(
                "ChatBotAction",
                [
                    "SimpleAction",
                    "ChooseOrderAction",
                ],
            ),
            Union(
                "ChatBotUpdate",
                ["ChooseOrdersUpdate", "ContactOperatorUpdate"],
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
