import pytest

from graphql import print_ast
from graphql.language.parser import parse
from hiku.export.graphql import export

from hiku.graph import Field, Graph, Interface, Link, Node, Option, Root, Union
from hiku.merge import QueryMerger
from hiku.types import Boolean, Integer, InterfaceRef, Optional, String, TypeRef, UnionRef, Sequence
from hiku.readers.graphql import read


def mock_resolve():
    ...


GRAPH = Graph(
        [
            Node(
                "User",
                [
                    Field("id", String, mock_resolve),
                    Field("name", String, mock_resolve, options=[
                        Option("capitalize", Optional[Boolean], default=False)
                    ]),
                    Link("info", TypeRef["Info"], mock_resolve, requires=None),
                    Link('playlist', Sequence[InterfaceRef['Media']], mock_resolve, requires=None)
                ],
            ),
            Node(
                "Info",
                [
                    Field("email", String, mock_resolve),
                    Field("phone", String, mock_resolve),
                    Link("transport", Optional[UnionRef["Transport"]], mock_resolve, requires=None)
                ],
            ),
            Node(
                "Context",
                [
                    Link("user", TypeRef["User"], mock_resolve, requires=None)
                ],
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
            Root(
                [Link("context", TypeRef["Context"], mock_resolve, requires=None)]
            ),
        ],
        interfaces=[
            Interface(
                "Media",
                [Field("duration", Integer, mock_resolve)],
            )
        ],
        unions=[Union("Transport", ["Car", "Bike"])],
    )


@pytest.mark.parametrize("src,result", [
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
])
def test_query_merger(src, result):
    exp = print_ast(parse(result)).strip()

    query = QueryMerger(GRAPH).merge(read(src))
    got = print_ast(export(query)).strip()

    assert got == exp



@pytest.mark.parametrize("src,result", [
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
])
def test_query_merger__unions(src, result):
    exp = print_ast(parse(result)).strip()
    query = read(src)
    query = QueryMerger(GRAPH).merge(query)
    got = print_ast(export(query)).strip()

    assert got == exp


@pytest.mark.parametrize("src,result", [
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
])
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
