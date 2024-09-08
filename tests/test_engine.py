import re
from typing import Any, List, Tuple
from collections import defaultdict

import pytest
from sqlalchemy import Column, ForeignKey
from sqlalchemy import Integer as SaInteger
from sqlalchemy import MetaData, Table, Unicode, create_engine
from sqlalchemy.pool import StaticPool

from hiku import query as q
from hiku.builder import Q, build
from hiku.denormalize.graphql import DenormalizeGraphQL
from hiku.endpoint.graphql import GraphQLEndpoint
from hiku.engine import Context, Engine, pass_context
from hiku.executors.sync import SyncExecutor
from hiku.graph import (Field, Graph, Interface, Link, Node, Nothing, Option,
                        Root, Union)
from hiku.readers.graphql import read
from hiku.result import denormalize
from hiku.sources.sqlalchemy import FieldsQuery
from hiku.types import (Boolean, Integer, InterfaceRef, Optional, Record, Sequence,
                        String, TypeRef, UnionRef)
from hiku.utils import ImmutableDict, listify

from .base import ANY, Mock, check_result


@listify
def id_field(fields, ids):
    for i in ids:
        yield [i for _ in fields]


OPTION_BEHAVIOUR = [
    (Option("op", None), {"op": 1812}, {"op": 1812}),
    (Option("op", None, default=None), {}, {"op": None}),
    (Option("op", None, default=None), {"op": 2340}, {"op": 2340}),
    (Option("op", None, default=3914), {}, {"op": 3914}),
    (Option("op", None, default=4254), {"op": None}, {"op": None}),
    (Option("op", None, default=1527), {"op": 8361}, {"op": 8361}),
]


def execute(graph, query_, ctx=None):
    engine = Engine(SyncExecutor())
    return engine.execute(graph, query_, ctx)


def execute_endpoint(graph, query):
    endpoint = GraphQLEndpoint(Engine(SyncExecutor()), graph)
    return endpoint.dispatch({"query": query})


def test_context():
    ctx = Context({"foo": "bar"})
    assert ctx["foo"] == "bar"
    assert "unknown" not in ctx
    with pytest.raises(KeyError, match="is not specified"):
        ctx["unknown"]
    with pytest.raises(TypeError, match="not support item assignment"):
        ctx["unknown"] = 42


def test_root_fields():
    f1 = Mock(return_value=["boiardo"])
    f2 = Mock(return_value=["isolde"])

    graph = Graph(
        [
            Root(
                [
                    Field("a", None, f1),
                    Field("b", None, f2),
                ]
            ),
        ]
    )

    result = execute(graph, build([Q.a, Q.b]))
    check_result(result, {"a": "boiardo", "b": "isolde"})

    f1.assert_called_once_with([q.Field("a")])
    f2.assert_called_once_with([q.Field("b")])


def test_node_fields():
    f1 = Mock(return_value=[1])
    f2 = Mock(return_value=[["harkis"]])
    f3 = Mock(return_value=[["slits"]])

    graph = Graph(
        [
            Node(
                "a",
                [
                    Field("b", None, f2),
                    Field("c", None, f3),
                ],
            ),
            Root(
                [
                    Link("d", Sequence[TypeRef["a"]], f1, requires=None),
                ]
            ),
        ]
    )

    result = execute(graph, build([Q.d[Q.b, Q.c]]))
    check_result(result, {"d": [{"b": "harkis", "c": "slits"}]})

    f1.assert_called_once_with()
    f2.assert_called_once_with([q.Field("b")], [1])
    f3.assert_called_once_with([q.Field("c")], [1])


def test_node_complex_fields():
    f1 = Mock(return_value=[1])
    f2 = Mock(return_value=[[{"f": "marshes"}]])
    f3 = Mock(return_value=[[{"g": "colline"}]])
    f4 = Mock(return_value=[[[{"h": "magi"}]]])

    graph = Graph(
        [
            Node(
                "a",
                [
                    Field("b", Optional[Record[{"f": Integer}]], f2),
                    Field("c", Record[{"g": Integer}], f3),
                    Field("d", Sequence[Record[{"h": Integer}]], f4),
                ],
            ),
            Root(
                [
                    Link("e", Sequence[TypeRef["a"]], f1, requires=None),
                ]
            ),
        ]
    )

    check_result(
        execute(graph, build([Q.e[Q.b[Q.f], Q.c[Q.g], Q.d[Q.h]]])),
        {
            "e": [
                {
                    "b": {"f": "marshes"},
                    "c": {"g": "colline"},
                    "d": [{"h": "magi"}],
                }
            ]
        },
    )

    f1.assert_called_once_with()
    f2.assert_called_once_with(
        [q.Link("b", q.Node([q.Field("f")]))],
        [1],
    )
    f3.assert_called_once_with(
        [q.Link("c", q.Node([q.Field("g")]))],
        [1],
    )
    f4.assert_called_once_with(
        [q.Link("d", q.Node([q.Field("h")]))],
        [1],
    )


def test_links():
    fb = Mock(return_value=[1])
    fc = Mock(return_value=[2])
    fi = Mock(return_value=[3])
    fd = Mock(return_value=[["boners"]])
    fe = Mock(return_value=[["julio"]])

    graph = Graph(
        [
            Node(
                "a",
                [
                    Field("d", None, fd),
                    Field("e", None, fe),
                ],
            ),
            Root(
                [
                    Field("i", None, fi),
                    Link("b", Sequence[TypeRef["a"]], fb, requires=None),
                    Link("c", Sequence[TypeRef["a"]], fc, requires="i"),
                ]
            ),
        ]
    )

    result = execute(graph, build([Q.b[Q.d], Q.c[Q.e]]))
    check_result(result, {"b": [{"d": "boners"}], "c": [{"e": "julio"}]})

    fi.assert_called_once_with([q.Field("i")])
    fb.assert_called_once_with()
    fc.assert_called_once_with(3)
    fd.assert_called_once_with([q.Field("d")], [1])
    fe.assert_called_once_with([q.Field("e")], [2])


def test_links_requires_list():
    db = {
        "song": {100: {"name": "fuel", "artist_id": 1, "album_id": 10}},
        "artist": {
            1: {"name": "Metallica"},
        },
        "album": {10: {"name": "Reload"}},
    }

    link_song = Mock(return_value=100)

    def link_song_info(
        reqs: List[ImmutableDict[str, Any]]
    ) -> List[ImmutableDict[str, Any]]:
        return reqs

    def song_fields(fields, song_ids):
        def get_fields(song_id):
            for f in fields:
                yield db["song"][song_id][f.name]

        return [list(get_fields(song_id)) for song_id in song_ids]

    def song_info_fields(fields, ids):
        def get_fields(id_):
            album_id = id_["album_id"]
            artist_id = id_["artist_id"]
            for f in fields:
                if f.name == "album_name":
                    yield db["album"][album_id]["name"]
                elif f.name == "artist_name":
                    yield db["artist"][artist_id]["name"]

        return [list(get_fields(id_)) for id_ in ids]

    graph = Graph(
        [
            Node(
                "SongInfo",
                [
                    Field("album_name", None, song_info_fields),
                    Field("artist_name", None, song_info_fields),
                ],
            ),
            Node(
                "Song",
                [
                    Field("id", None, song_fields),
                    Field("name", None, song_fields),
                    Field("album_id", None, song_fields),
                    Field("artist_id", None, song_fields),
                    Link(
                        "info",
                        TypeRef["SongInfo"],
                        link_song_info,
                        requires=["album_id", "artist_id"],
                    ),
                ],
            ),
            Root(
                [
                    Link("song", TypeRef["Song"], link_song, requires=None),
                ]
            ),
        ]
    )

    query = build(
        [
            Q.song[
                Q.info[
                    Q.album_name,
                    Q.artist_name,
                ]
            ]
        ]
    )
    result = execute(graph, query)
    check_result(
        result,
        {
            "song": {
                "info": {"album_name": "Reload", "artist_name": "Metallica"}
            }
        },
    )


def test_links_requires_list_sa():
    SA_ENGINE_KEY = "sa-engine"
    metadata = MetaData()

    song_table = Table(
        "song",
        metadata,
        Column("id", SaInteger, primary_key=True, autoincrement=True),
        Column("name", Unicode),
        Column("album_id", ForeignKey("album.id")),
        Column("artist_id", ForeignKey("artist.id")),
    )

    album_table = Table(
        "album",
        metadata,
        Column("id", SaInteger, primary_key=True, autoincrement=True),
        Column("name", Unicode),
    )

    artist_table = Table(
        "artist",
        metadata,
        Column("id", SaInteger, primary_key=True, autoincrement=True),
        Column("name", Unicode),
    )

    data = {
        "song": [{"id": 100, "name": "fuel", "artist_id": 1, "album_id": 10}],
        "artist": [{"id": 1, "name": "Metallica"}],
        "album": [{"id": 10, "name": "Reload"}],
    }

    def setup_db(db_engine):
        metadata.create_all(db_engine)
        for row in data["artist"]:
            db_engine.execute(artist_table.insert(), row)
        for row in data["album"]:
            db_engine.execute(album_table.insert(), row)
        for row in data["song"]:
            db_engine.execute(song_table.insert(), row)

    sa_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    setup_db(sa_engine)

    ctx = {SA_ENGINE_KEY: sa_engine}

    link_song = Mock(return_value=100)

    def link_song_info(reqs: List[Tuple]):
        return reqs

    def link_artist(ids):
        return ids

    @pass_context
    def song_info_fields(ctx, fields, ids):
        db = ctx[SA_ENGINE_KEY]

        def get_fields(id_):
            album_id = id_["album_id"]
            artist_id = id_["artist_id"]
            album = db.execute(
                album_table.select().where(album_table.c.id == album_id)
            ).first()
            artist = db.execute(
                artist_table.select().where(artist_table.c.id == artist_id)
            ).first()

            for f in fields:
                if f.name == "album_name":
                    yield album.name
                elif f.name == "artist_name":
                    yield artist.name

        return [list(get_fields(id_)) for id_ in ids]

    song_query = FieldsQuery(SA_ENGINE_KEY, song_table)
    artist_query = FieldsQuery(SA_ENGINE_KEY, artist_table)

    graph = Graph(
        [
            Node(
                "SongInfo",
                [
                    Field("album_name", None, song_info_fields),
                    Field("artist_name", None, song_info_fields),
                ],
            ),
            Node(
                "Artist",
                [
                    Field("id", None, artist_query),
                ],
            ),
            Node(
                "Song",
                [
                    Field("id", None, song_query),
                    Field("name", None, song_query),
                    Field("album_id", None, song_query),
                    Field("artist_id", None, song_query),
                    Link(
                        "info",
                        TypeRef["SongInfo"],
                        link_song_info,
                        requires=["album_id", "artist_id"],
                    ),
                    Link(
                        "artist",
                        TypeRef["Artist"],
                        link_artist,
                        requires="artist_id",
                    ),
                ],
            ),
            Root(
                [
                    Link("song", TypeRef["Song"], link_song, requires=None),
                ]
            ),
        ]
    )

    query = build(
        [
            Q.song[
                Q.info[
                    Q.album_name,
                    Q.artist_name,
                ],
                # we are querying 'artist' here to test that its requires does not
                # affect the requires of the 'info' link
                Q.artist[Q.id,],
            ]
        ]
    )
    norm_result = execute(graph, query, ctx)
    result = DenormalizeGraphQL(graph, norm_result, "query").process(query)
    check_result(
        result,
        {
            "song": {
                "info": {"album_name": "Reload", "artist_name": "Metallica"},
                "artist": {"id": 1},
            }
        },
    )


@pytest.mark.parametrize("option, args, result", OPTION_BEHAVIOUR)
def test_field_option_valid(option, args, result):
    f = Mock(return_value=["baking"])
    graph = Graph(
        [
            Root(
                [
                    Field("auslese", None, f, options=[option]),
                ]
            ),
        ]
    )
    check_result(
        execute(graph, build([Q.auslese(**args)])), {"auslese": "baking"}
    )
    f.assert_called_once_with([q.Field("auslese", options=result)])


def test_field_option_unknown():
    test_field_option_valid(
        Option("inked", None), {"inked": 2340, "unknown": 8775}, {"inked": 2340}
    )


def test_field_option_missing():
    graph = Graph(
        [
            Root(
                [
                    Field(
                        "poofy", None, Mock(), options=[Option("mohism", None)]
                    ),
                ]
            ),
        ]
    )
    with pytest.raises(TypeError) as err:
        execute(graph, build([Q.poofy]))
    err.match(
        r'^Required option "mohism" for Field\(\'poofy\', '
        r"(.*) was not provided$"
    )


@pytest.mark.parametrize("option, args, result", OPTION_BEHAVIOUR)
def test_link_option_valid(option, args, result):
    f1 = Mock(return_value=[1])
    f2 = Mock(return_value=[["aunder"]])
    graph = Graph(
        [
            Node(
                "a",
                [
                    Field("c", None, f2),
                ],
            ),
            Root(
                [
                    Link(
                        "b",
                        Sequence[TypeRef["a"]],
                        f1,
                        requires=None,
                        options=[option],
                    ),
                ]
            ),
        ]
    )
    check_result(
        execute(graph, build([Q.b(**args)[Q.c]])), {"b": [{"c": "aunder"}]}
    )
    f1.assert_called_once_with(result)
    f2.assert_called_once_with([q.Field("c")], [1])


def test_link_option_unknown():
    test_link_option_valid(
        Option("oleic", None), {"oleic": 2340, "unknown": 8775}, {"oleic": 2340}
    )


def test_link_option_missing():
    graph = Graph(
        [
            Node(
                "slices",
                [
                    Field("papeete", None, Mock()),
                ],
            ),
            Root(
                [
                    Link(
                        "eclairs",
                        Sequence[TypeRef["slices"]],
                        Mock(),
                        requires=None,
                        options=[Option("nocks", None)],
                    ),
                ]
            ),
        ]
    )
    with pytest.raises(TypeError) as err:
        execute(graph, build([Q.eclairs[Q.papeete]]))
    err.match(
        r'^Required option "nocks" for Link\(\'eclairs\', '
        r"(.*) was not provided$"
    )


def test_pass_context_field():
    f = pass_context(Mock(return_value=["boiardo"]))

    graph = Graph(
        [
            Root(
                [
                    Field("a", None, f),
                ]
            ),
        ]
    )

    check_result(
        execute(graph, build([Q.a]), {"vetch": "shadier"}), {"a": "boiardo"}
    )

    f.assert_called_once_with(ANY, [q.Field("a")])

    ctx = f.call_args[0][0]
    assert isinstance(ctx, Context)
    assert ctx["vetch"] == "shadier"
    with pytest.raises(KeyError) as err:
        _ = ctx["invalid"]  # noqa
    err.match("is not specified in the query context")


def test_pass_context_link():
    f1 = pass_context(Mock(return_value=[1]))
    f2 = Mock(return_value=[["boners"]])

    graph = Graph(
        [
            Node(
                "a",
                [
                    Field("b", None, f2),
                ],
            ),
            Root(
                [
                    Link("c", Sequence[TypeRef["a"]], f1, requires=None),
                ]
            ),
        ]
    )

    result = execute(graph, build([Q.c[Q.b]]), {"fibs": "dossil"})
    check_result(result, {"c": [{"b": "boners"}]})

    f1.assert_called_once_with(ANY)
    f2.assert_called_once_with([q.Field("b")], [1])

    ctx = f1.call_args[0][0]
    assert isinstance(ctx, Context)
    assert ctx["fibs"] == "dossil"
    with pytest.raises(KeyError) as err:
        _ = ctx["invalid"]  # noqa
    err.match("is not specified in the query context")


def test_node_link_without_requirements():
    f1 = Mock(return_value=[1])
    f2 = Mock(return_value=[2])
    f3 = Mock(return_value=[["arnhild"]])

    graph = Graph(
        [
            Node(
                "a",
                [
                    Field("c", None, f3),
                ],
            ),
            Node(
                "b",
                [
                    Link("d", Sequence[TypeRef["a"]], f2, requires=None),
                ],
            ),
            Root(
                [
                    Link("e", Sequence[TypeRef["b"]], f1, requires=None),
                ]
            ),
        ]
    )

    result = execute(graph, build([Q.e[Q.d[Q.c]]]))
    check_result(result, {"e": [{"d": [{"c": "arnhild"}]}]})

    f1.assert_called_once_with()
    f2.assert_called_once_with()
    f3.assert_called_once_with([q.Field("c")], [2])


@pytest.mark.parametrize("value", [1, [], [1, 2]])
def test_root_field_func_result_validation(value):
    with pytest.raises(TypeError) as err:
        execute(
            Graph(
                [
                    Root(
                        [
                            Field("a", None, Mock(return_value=value)),
                        ]
                    ),
                ]
            ),
            build([Q.a]),
        )
    err.match(
        re.escape(
            "Can't store field values, node: '__root__', fields: ['a'], "
            "expected: list (len: 1), returned: {value!r}".format(value=value)
        )
    )


@pytest.mark.parametrize(
    "value", [1, [], [1, 2], [[], []], [[1], []], [[], [2]]]
)
def test_node_field_func_result_validation(value):
    with pytest.raises(TypeError) as err:
        execute(
            Graph(
                [
                    Node(
                        "a",
                        [
                            Field("b", None, Mock(return_value=value)),
                        ],
                    ),
                    Root(
                        [
                            Link(
                                "c",
                                Sequence[TypeRef["a"]],
                                Mock(return_value=[1, 2]),
                                requires=None,
                            ),
                        ]
                    ),
                ]
            ),
            build([Q.c[Q.b]]),
        )
    err.match(
        re.escape(
            "Can't store field values, node: 'a', fields: ['b'], "
            "expected: list (len: 2) of lists (len: 1), returned: {value!r}".format(
                value=value
            )
        )
    )


def test_root_link_many_func_result_validation():
    with pytest.raises(TypeError) as err:
        execute(
            Graph(
                [
                    Node(
                        "a",
                        [
                            Field("b", None, Mock(return_value=[[3], [4]])),
                        ],
                    ),
                    Root(
                        [
                            Link(
                                "c",
                                Sequence[TypeRef["a"]],
                                Mock(return_value=123),
                                requires=None,
                            ),
                        ]
                    ),
                ]
            ),
            build([Q.c[Q.b]]),
        )
    err.match(
        re.escape(
            "Can't store link values, node: '__root__', link: 'c', "
            "expected: list, returned: 123"
        )
    )


@pytest.mark.parametrize("value", [1, [], [1, 2, 3]])
def test_node_link_one_func_result_validation(value):
    with pytest.raises(TypeError) as err:
        execute(
            Graph(
                [
                    Node(
                        "a", [Field("b", None, Mock(return_value=[[1], [2]]))]
                    ),
                    Node(
                        "c",
                        [
                            Field("d", None, Mock(return_value=[[3], [4]])),
                            Link(
                                "e",
                                TypeRef["a"],
                                Mock(return_value=value),
                                requires="d",
                            ),
                        ],
                    ),
                    Root(
                        [
                            Link(
                                "f",
                                Sequence[TypeRef["c"]],
                                Mock(return_value=[1, 2]),
                                requires=None,
                            ),
                        ]
                    ),
                ]
            ),
            build([Q.f[Q.e[Q.b]]]),
        )
    err.match(
        re.escape(
            "Can't store link values, node: 'c', link: 'e', expected: "
            "list (len: 2), returned: {!r}".format(value)
        )
    )


@pytest.mark.parametrize("value", [1, [], [1, []], [[], 2], [[], [], []]])
def test_node_link_many_func_result_validation(value):
    with pytest.raises(TypeError) as err:
        execute(
            Graph(
                [
                    Node(
                        "a", [Field("b", None, Mock(return_value=[[1], [2]]))]
                    ),
                    Node(
                        "c",
                        [
                            Field("d", None, Mock(return_value=[[3], [4]])),
                            Link(
                                "e",
                                Sequence[TypeRef["a"]],
                                Mock(return_value=value),
                                requires="d",
                            ),
                        ],
                    ),
                    Root(
                        [
                            Link(
                                "f",
                                Sequence[TypeRef["c"]],
                                Mock(return_value=[1, 2]),
                                requires=None,
                            ),
                        ]
                    ),
                ]
            ),
            build([Q.f[Q.e[Q.b]]]),
        )
    err.match(
        re.escape(
            "Can't store link values, node: 'c', link: 'e', expected: "
            "list (len: 2) of lists, returned: {!r}".format(value)
        )
    )


def test_root_field_alias():
    data = {"a": 42}

    def root_fields(fields):
        return [data[f.name] for f in fields]

    graph = Graph(
        [
            Root(
                [
                    Field("a", None, root_fields),
                ]
            ),
        ]
    )
    result = execute(
        graph,
        q.Node(
            [
                q.Field("a", alias="a1"),
                q.Field("a", alias="a2"),
            ]
        ),
    )
    check_result(result, {"a1": 42, "a2": 42})


def test_node_field_alias():
    data = {"x1": {"a": 42}}

    @listify
    def x_fields(fields, ids):
        for i in ids:
            yield [data[i][f.name] for f in fields]

    graph = Graph(
        [
            Node(
                "X",
                [
                    Field("a", None, x_fields),
                ],
            ),
            Root(
                [
                    Link("x", TypeRef["X"], lambda: "x1", requires=None),
                ]
            ),
        ]
    )
    result = execute(
        graph,
        q.Node(
            [
                q.Link(
                    "x",
                    q.Node(
                        [
                            q.Field("a", alias="a1"),
                            q.Field("a", alias="a2"),
                        ]
                    ),
                ),
            ]
        ),
    )
    check_result(result, {"x": {"a1": 42, "a2": 42}})


def test_root_link_alias():
    data = {
        "xN": {"a": 1, "b": 2},
    }

    @listify
    def x_fields(fields, ids):
        for i in ids:
            yield [data[i][f.name] for f in fields]

    graph = Graph(
        [
            Node(
                "X",
                [
                    Field("a", None, x_fields),
                    Field("b", None, x_fields),
                ],
            ),
            Root(
                [
                    Link("x", TypeRef["X"], lambda: "xN", requires=None),
                ]
            ),
        ]
    )
    result = execute(
        graph,
        q.Node(
            [
                q.Link("x", q.Node([q.Field("a")]), alias="x1"),
                q.Link("x", q.Node([q.Field("b")]), alias="x2"),
            ]
        ),
    )
    check_result(
        result,
        {
            "x1": {"a": 1},
            "x2": {"b": 2},
        },
    )


def test_node_link_alias():
    data = {
        "yN": {"a": 1, "b": 2},
    }
    x2y = {"xN": "yN"}

    @listify
    def y_fields(fields, ids):
        for i in ids:
            yield [data[i][f.name] for f in fields]

    graph = Graph(
        [
            Node(
                "Y",
                [
                    Field("a", None, y_fields),
                    Field("b", None, y_fields),
                ],
            ),
            Node(
                "X",
                [
                    Field("id", None, id_field),
                    Link(
                        "y",
                        TypeRef["Y"],
                        lambda ids: [x2y[i] for i in ids],
                        requires="id",
                    ),
                ],
            ),
            Root(
                [
                    Link("x", TypeRef["X"], lambda: "xN", requires=None),
                ]
            ),
        ]
    )
    result = execute(
        graph,
        q.Node(
            [
                q.Link(
                    "x",
                    q.Node(
                        [
                            q.Link("y", q.Node([q.Field("a")]), alias="y1"),
                            q.Link("y", q.Node([q.Field("b")]), alias="y2"),
                        ]
                    ),
                ),
            ]
        ),
    )
    check_result(
        result,
        {
            "x": {
                "y1": {"a": 1},
                "y2": {"b": 2},
            }
        },
    )


def test_conflicting_fields():
    x_data = {"xN": {"a": 42}}

    @listify
    def x_fields(fields, ids):
        for i in ids:
            yield [
                "{}-{}".format(x_data[i][f.name], f.options["k"])
                for f in fields
            ]

    graph = Graph(
        [
            Node(
                "X",
                [
                    Field("a", None, x_fields, options=[Option("k", Integer)]),
                ],
            ),
            Root(
                [
                    Link("x1", TypeRef["X"], lambda: "xN", requires=None),
                    Link("x2", TypeRef["X"], lambda: "xN", requires=None),
                ]
            ),
        ]
    )

    result = execute(
        graph,
        q.Node(
            [
                q.Link("x1", q.Node([q.Field("a", options={"k": 1})])),
                q.Link("x2", q.Node([q.Field("a", options={"k": 2})])),
            ]
        ),
    )
    check_result(
        result,
        {
            "x1": {"a": "42-1"},
            "x2": {"a": "42-2"},
        },
    )


def test_conflicting_links():
    data = {
        "yA": {"a": 1, "b": 2},
        "yB": {"a": 3, "b": 4},
        "yC": {"a": 5, "b": 6},
    }
    x2y = {"xN": ["yA", "yB", "yC"]}

    @listify
    def y_fields(fields, ids):
        for i in ids:
            yield [data[i][f.name] for f in fields]

    @listify
    def x_to_y_link(ids, options):
        for i in ids:
            yield [y for y in x2y[i] if y not in options["exclude"]]

    graph = Graph(
        [
            Node(
                "Y",
                [
                    Field("a", None, y_fields),
                    Field("b", None, y_fields),
                ],
            ),
            Node(
                "X",
                [
                    Field("id", None, id_field),
                    Link(
                        "y",
                        Sequence[TypeRef["Y"]],
                        x_to_y_link,
                        requires="id",
                        options=[Option("exclude", None)],
                    ),
                ],
            ),
            Root(
                [
                    Link("x1", TypeRef["X"], lambda: "xN", requires=None),
                    Link("x2", TypeRef["X"], lambda: "xN", requires=None),
                ]
            ),
        ]
    )
    result = execute(
        graph,
        q.Node(
            [
                q.Link(
                    "x1",
                    q.Node(
                        [
                            q.Link(
                                "y",
                                q.Node([q.Field("a")]),
                                options={"exclude": ["yA"]},
                            ),
                        ]
                    ),
                ),
                q.Link(
                    "x2",
                    q.Node(
                        [
                            q.Link(
                                "y",
                                q.Node([q.Field("b")]),
                                options={"exclude": ["yC"]},
                            ),
                        ]
                    ),
                ),
            ]
        ),
    )
    check_result(
        result,
        {
            "x1": {"y": [{"a": 3}, {"a": 5}]},
            "x2": {"y": [{"b": 2}, {"b": 4}]},
        },
    )


def test_process_ordered_node():
    ordering = []

    def f1(fields):
        names = tuple(f.name for f in fields)
        ordering.append(names)
        return names

    def f2(fields):
        return f1(fields)

    def f3():
        ordering.append("x1")
        return "x1"

    @listify
    def f4(fields, ids):
        for i in ids:
            yield ["{}-e".format(i) for _ in fields]

    graph = Graph(
        [
            Node(
                "X",
                [
                    Field("e", None, f4),
                ],
            ),
            Root(
                [
                    Field("a", None, f1),
                    Field("b", None, f1),
                    Field("c", None, f2),
                    Field("d", None, f2),
                    Link("x", TypeRef["X"], f3, requires=None),
                ]
            ),
        ]
    )
    query = q.Node(
        [
            q.Field("d"),
            q.Field("b"),
            q.Field("a"),
            q.Link(
                "x",
                q.Node(
                    [
                        q.Field("e"),
                    ]
                ),
            ),
            q.Field("c"),
        ],
        ordered=True,
    )

    result = execute(graph, query)
    check_result(
        result,
        {
            "a": "a",
            "b": "b",
            "c": "c",
            "d": "d",
            "x": {
                "e": "x1-e",
            },
        },
    )
    assert ordering == [("d",), ("b", "a"), "x1", ("c",)]


def test_falsy_link_result():
    x_fields = Mock(return_value=[[42]])
    graph = Graph(
        [
            Node(
                "X",
                [
                    Field("a", None, x_fields),
                ],
            ),
            Root(
                [
                    Link("x", TypeRef["X"], lambda: 0, requires=None),
                ]
            ),
        ]
    )
    result = execute(
        graph,
        q.Node(
            [
                q.Link("x", q.Node([q.Field("a")])),
            ]
        ),
    )
    assert denormalize(graph, result) == {"x": {"a": 42}}
    x_fields.assert_called_once_with([q.Field("a")], [0])


def test_root_link_with_sequence_to_optional_type_ref():
    def a_fields(fields, ids):
        def get_fields(f, id_):
            assert id_ is not None and id_ is not Nothing
            if f.name == "a":
                return 42
            raise AssertionError("Unexpected field: {}".format(f))

        return [[get_fields(f, id_) for f in fields] for id_ in ids]

    graph = Graph(
        [
            Node("A", [Field("a", String, a_fields)]),
            Root(
                [
                    Link(
                        "aa",
                        Sequence[Optional[TypeRef["A"]]],
                        lambda: [1, Nothing],
                        requires=None,
                    )
                ]
            ),
        ]
    )

    result = execute(
        graph,
        q.Node(
            [
                q.Link("aa", q.Node([q.Field("a")])),
            ]
        ),
    )
    assert denormalize(graph, result) == {"aa": [{"a": 42}, None]}


def test_root_link_with_sequence_to_optional_union_ref():
    def a_fields(fields, ids):
        def get_fields(f, id_):
            assert id_ is not None and id_ is not Nothing
            if f.name == "a":
                return 42
            if f.name == "b":
                return 24
            raise AssertionError("Unexpected field: {}".format(f))

        return [[get_fields(f, id_) for f in fields] for id_ in ids]

    graph = Graph(
        [
            Node("A1", [Field("a", String, a_fields)]),
            Node("A2", [Field("b", String, a_fields)]),
            Root(
                [
                    Link(
                        "aa",
                        Sequence[Optional[UnionRef["A"]]],
                        lambda: [
                            (1, TypeRef["A1"]),
                            Nothing
                        ],
                        requires=None,
                    )
                ]
            ),
        ],
        unions=[
            Union('A', ['A1', 'A2']),
        ]
    )

    query = read("""
        { aa {
             ... on A1 { a }
             ... on A2 { b }
          }
        }
        """)
    result = execute(
        graph,
        query,
    )

    assert DenormalizeGraphQL(graph, result, "query").process(query) == {"aa": [{"a": 42}, None]}


# TODO: test typeref
def test_non_root_link_with_sequence_to_optional_type_ref():
    def a_fields(fields, ids):
        def get_fields(f, id_):
            assert id_ is not None and id_ is not Nothing
            if f.name == "a":
                return 42
            raise AssertionError("Unexpected field: {}".format(f))

        return [[get_fields(f, id_) for f in fields] for id_ in ids]

    def b_fields(fields, ids):
        def get_fields(f, id_):
            assert id_ is not None and id_ is not Nothing
            if f.name == "b":
                return 24
            raise AssertionError("Unexpected field: {}".format(f))

        return [[get_fields(f, id_) for f in fields] for id_ in ids]

    @listify
    def link_b2(ids):
        for _ in ids:
            yield [1, Nothing]

    graph = Graph(
        [
            Node(
                "A",
                [
                    Field("a", String, a_fields),
                    Link(
                        "b1",
                        Sequence[Optional[TypeRef["B"]]],
                        lambda: [1, Nothing],
                        requires=None,
                    ),
                    # same as 'b' but with requires
                    Link(
                        "b2",
                        Sequence[Optional[TypeRef["B"]]],
                        link_b2,
                        requires="a",
                    ),
                ],
            ),
            Node("B", [Field("b", String, b_fields)]),
            Root([Link("a_root", TypeRef["A"], lambda: 1, requires=None)]),
        ]
    )

    result = execute(
        graph,
        q.Node(
            [
                q.Link(
                    "a_root",
                    q.Node(
                        [
                            q.Field("a"),
                            q.Link("b1", q.Node([q.Field("b")])),
                            q.Link("b2", q.Node([q.Field("b")])),
                        ]
                    ),
                ),
            ]
        ),
    )
    assert denormalize(graph, result) == {
        "a_root": {"a": 42, "b1": [{"b": 24}, None], "b2": [{"b": 24}, None]}
    }


def test_merge_query__fragments():
    num_link_user = 0
    num_resolve_id = 0
    num_resolve_name = 0

    def resolve_user(fields, ids):
        def get_field(f, id_):
            if f.name == "name":
                nonlocal num_resolve_name
                num_resolve_name += 1
                return "John"
            elif f.name == "id":
                nonlocal num_resolve_id
                num_resolve_id += 1
                return id_

        return [[get_field(f, id_) for f in fields] for id_ in ids]

    def link_user():
        nonlocal num_link_user
        num_link_user += 1
        return 1

    graph = Graph(
        [
            Node(
                "User",
                [
                    Field("id", String, resolve_user),
                    Field("name", String, resolve_user),
                ],
            ),
            Node(
                "Context",
                [Link("user", TypeRef["User"], link_user, requires=None)],
            ),
            Root(
                [Link("context", TypeRef["Context"], lambda: 1, requires=None)]
            ),
        ]
    )

    query = """
    query GetUser {
        context {
            user { id }
            ... on Context {
                user { ... on User { id name } }
            }
        }
    }
    """

    data = execute_endpoint(graph, query)["data"]

    assert num_link_user == 1
    assert num_resolve_id == 1
    assert num_resolve_name == 1
    assert data == {"context": {"user": {"id": 1, "name": "John"}}}


@pytest.mark.parametrize("query", [
    pytest.param(
        """
        query GetUser2 {
            context {
                user {
                    id
                }
                ... on BaseContext {
                    user { name }
                }
                ... on MyContext {
                    user { name }
                    balance
                }
            }
        }
        """,
        id="one level fragments"
    ),
    pytest.param(
        """
        query GetUser {
            context {
                ...ContextFragment
            }
        }
        fragment ContextFragment on Context {
            user {
                id
            }
            ... on BaseContext {
                user { name }
            }
            ... on MyContext {
                user { name }
                balance
            }
        }
        """,
        id="nested fragments",
    ),
    pytest.param(
        """
        query GetUser {
            context {
                ... on MyContext {
                    user { name }
                }
                ...ContextFragment
            }
        }
        fragment ContextFragment on Context {
            user {
                id
            }
            ... on BaseContext {
                user { name }
            }
            ... on MyContext {
                balance
            }
        }
        """,
        id="nested + neighbour fragments",
    ),
])
def test_merge_query__interface_fragments(query):
    num_link_user = 0
    num_resolve_id = 0
    num_resolve_name = 0

    def resolve_user(fields, ids):
        def get_field(f, id_):
            if f.name == "name":
                nonlocal num_resolve_name
                num_resolve_name += 1
                return "John"
            elif f.name == "id":
                nonlocal num_resolve_id
                num_resolve_id += 1
                return id_

        return [[get_field(f, id_) for f in fields] for id_ in ids]

    def link_user():
        nonlocal num_link_user
        num_link_user += 1
        return 1

    graph = Graph(
        [
            Node(
                "User",
                [
                    Field("id", String, resolve_user),
                    Field("name", String, resolve_user),
                ],
            ),
            Node(
                "MyContext",
                [
                    Link("user", TypeRef["User"], link_user, requires=None),
                    Field("balance", Integer, lambda fields, ids: [[100]]),
                ],
                implements=["Context"],
            ),
            Node(
                "BaseContext",
                [
                    Link("user", TypeRef["User"], link_user, requires=None),
                ],
                implements=["Context"],
            ),
            Root(
                [
                    Link(
                        "context",
                        InterfaceRef["Context"],
                        lambda: (1, TypeRef["MyContext"]),
                        requires=None,
                    )
                ]
            ),
        ],
        interfaces=[
            Interface(
                "Context",
                [Link("user", TypeRef["User"], lambda x: x, requires=None)],
            )
        ],
    )

    result = execute_endpoint(graph, query)
    data = result["data"]

    assert num_link_user == 1
    assert num_resolve_id == 1
    assert num_resolve_name == 1
    assert data == {
        "context": {"user": {"id": 1, "name": "John"}, "balance": 100}
    }


@pytest.mark.parametrize("query", [
    pytest.param(
        """
        query GetUser {
            contexts {
                ... on BaseContext { user { name } }
                ... on MyContext { user { id name } }
                ... on MyContext { balance }
            }
        }
        """,
        id="one level fragments"),
    pytest.param(
        """
        query GetUser {
            contexts {
                ...ContextsFragment
            }
        }
        fragment ContextsFragment on Context {
            ... on BaseContext { user { name } }
            ... on MyContext { user { id name } }
            ... on MyContext { balance }
        }
        """,
        id="nested fragments",

    ),
    pytest.param(
        """
        query GetUser {
            contexts {
                ... on MyContext { balance }
                ...ContextsFragment
            }
        }
        fragment ContextsFragment on Context {
            ... on BaseContext { user { name } }
            ... on MyContext { user { id name } }
        }
        """,
        id="nested + neighbour fragments",
    ),
])
def test_merge_query__union_fragments(query):
    num_link_user = 0
    num_resolve_id = 0
    num_resolve_name = 0

    def resolve_user(fields, ids):
        def get_field(f, id_):
            if f.name == "name":
                nonlocal num_resolve_name
                num_resolve_name += 1
                return "John" + str(id_)
            elif f.name == "id":
                nonlocal num_resolve_id
                num_resolve_id += 1
                return id_

        return [[get_field(f, id_) for f in fields] for id_ in ids]

    def link_user(ids):
        nonlocal num_link_user
        num_link_user += 1
        return ids

    graph = Graph(
        [
            Node(
                "User",
                [
                    Field("id", String, resolve_user),
                    Field("name", String, resolve_user),
                ],
            ),
            Node(
                "MyContext",
                [
                    Field("user_id", Integer, lambda fields, ids: [ids]),
                    Link(
                        "user", TypeRef["User"], link_user, requires="user_id"
                    ),
                    Field("balance", Integer, lambda fields, ids: [[100]]),
                ],
            ),
            Node(
                "BaseContext",
                [
                    Field("user_id", Integer, lambda fields, ids: [ids]),
                    Link(
                        "user", TypeRef["User"], link_user, requires="user_id"
                    ),
                ],
            ),
            Root(
                [
                    Link(
                        "contexts",
                        Sequence[UnionRef["Context"]],
                        lambda: [
                            (1, TypeRef["MyContext"]),
                            (2, TypeRef["BaseContext"]),
                        ],
                        requires=None,
                    )
                ]
            ),
        ],
        unions=[Union("Context", ["BaseContext", "MyContext"])],
    )

    result = execute_endpoint(graph, query)
    data = result["data"]

    assert num_link_user == 2
    assert num_resolve_id == 1
    assert num_resolve_name == 2
    assert data == {
        "contexts": [
            {"user": {"id": 1, "name": "John1"}, "balance": 100},
            {
                "user": {"name": "John2"},
            },
        ]
    }


def test_merge_query__fields_and_nested_fragments() -> None:
    call_count = defaultdict(int)

    def _count_calls(func):
        def wrapper(*args, **kwargs):
            if func.__name__.startswith("resolve"):
                for field in args[0]:
                    key = f'{func.__name__}:{field.name}'
                    call_count[key] += 1
            else:
                call_count[func.__name__] += 1
            return func(*args, **kwargs)

        return wrapper

    @_count_calls
    def resolve_user(fields, ids) -> List[Any]:
        def get_field(f, id_) -> Any:
            if f.name == "name":
                if f.options.get("capitalize", False):
                    return "John"
                return "john"
            elif f.name == "id":
                return id_

        return [[get_field(f, id_) for f in fields] for id_ in ids]

    @_count_calls
    def resolve_info(fields, ids) -> List[Any]:
        def get_field(f, id_) -> Any:
            if f.name == "email":
                return "john@example.com"
            elif f.name == "phone":
                return "+1234567890"

        return [[get_field(f, id_) for f in fields] for id_ in ids]

    @_count_calls
    def link_user() -> int:
        return 1

    @_count_calls
    def link_info() -> int:
        return 100

    graph = Graph(
        [
            Node(
                "User",
                [
                    Field("id", String, resolve_user),
                    Field("name", String, resolve_user, options=[
                        Option("capitalize", Optional[Boolean], default=False)
                    ]),
                    Link("info", TypeRef["Info"], link_info, requires=None)
                ],
            ),
            Node(
                "Info",
                [
                    Field("email", String, resolve_info),
                    Field("phone", String, resolve_info),
                ],
            ),
            Node(
                "Context",
                [
                    Link("user", TypeRef["User"], link_user, requires=None)
                ],
            ),
            Root(
                [Link("context", TypeRef["Context"], lambda: 100, requires=None)]
            ),
        ]
    )

    query = """
    query GetUser {
        context {
            user {
                id
                name
                capName: name(capitalize: true)
            }
            ...ContextFragment
        }
    }

    fragment ContextFragment on Context {
        ...ContextAFragment
        ...ContextBFragment
    }

    fragment ContextAFragment on Context {
        user {
            id
            name
            ...UserFragmentA
            ...UserFragmentB
            ... on User {
                id
            }
        }
    }

    fragment ContextBFragment on Context {
        user {
            id
            capName: name(capitalize: true)
        }
    }

    fragment UserFragmentA on User {
        id
        info {
            email
        }
    }

    fragment UserFragmentB on User {
        id
        name
        capName: name(capitalize: true)
        info {
            phone
        }
    }
    """

    result = execute_endpoint(graph, query)
    data = result["data"]
    assert data == {
        "context": {
            "user": {
                "id": 1,
                "name": "john",
                "capName": "John",
                "info": {"email": "john@example.com", "phone": "+1234567890"}
            }
        }
    }


def test_merge_query__only_nested_fragments() -> None:
    def resolve_user(fields, ids) -> List[Any]:
        def get_field(f, id_) -> Any:
            if f.name == "name":
                if f.options.get("capitalize", False):
                    return "John"
                return "john"
            elif f.name == "id":
                return id_

        return [[get_field(f, id_) for f in fields] for id_ in ids]

    graph = Graph(
        [
            Node(
                "User",
                [
                    Field("id", String, resolve_user),
                    Field("name", String, resolve_user, options=[
                        Option("capitalize", Optional[Boolean], default=False)
                    ]),
                ],
            ),
            Node(
                "Context",
                [
                    Link("user", TypeRef["User"], lambda: 1, requires=None)
                ],
            ),
            Root(
                [Link("context", TypeRef["Context"], lambda: 100, requires=None)]
            ),
        ]
    )

    query = """
    query GetUser {
        context {
            ...ContextFragment
        }
    }

    fragment ContextFragment on Context {
        ...ContextAFragment
        ...ContextBFragment
    }

    fragment ContextAFragment on Context {
        user {
            id
            name
        }
    }

    fragment ContextBFragment on Context {
        user {
            id
            capName: name(capitalize: true)
        }
    }
    """

    result = execute_endpoint(graph, query)
    data = result["data"]
    assert data == {
        "context": {
            "user": {
                "id": 1,
                "name": "john",
                "capName": "John",
            }
        }
    }


def test_merge_query__complex_field_fragment() -> None:
    def point_func(fields):
        return [{
            "x": 1,
            "y": 2,
        }]

    graph = Graph([
        Root([
            Field('point', TypeRef["Point"], point_func),
        ]),
    ], data_types={
        'Point': Record[{
            'x': Integer,
            'y': Integer,
        }],
    })

    query = """
    query GetPoint {
        point {
            ...PointFragment
        }
    }

    fragment PointFragment on User {
        x y
    }
    """

    data = execute_endpoint(graph, query)["data"]

    assert data == {"point": {"x": 1, "y": 2}}