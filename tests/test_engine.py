import re

from concurrent.futures import ThreadPoolExecutor
from typing import (
    List,
    Tuple,
    Any,
)

import pytest

from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer as SaInteger,
    Unicode,
    ForeignKey,
    create_engine,
)
from sqlalchemy.pool import StaticPool

from hiku import query as q
from hiku.readers.graphql import read
from hiku.denormalize.graphql import DenormalizeGraphQL
from hiku.executors.threads import ThreadsExecutor
from hiku.graph import Graph, Node, Field, Link, Nothing, Option, Root
from hiku.sources.sqlalchemy import FieldsQuery
from hiku.types import Record, Sequence, Integer, Optional, String, TypeRef
from hiku.utils import (
    listify,
    ImmutableDict,
)
from hiku.engine import Engine, pass_context, Context
from hiku.result import denormalize
from hiku.builder import build, Q
from hiku.executors.sync import SyncExecutor

from .base import check_result, ANY, Mock


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
    return engine.execute(graph, query_, ctx=ctx)


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

    thread_pool = ThreadPoolExecutor(2)

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

    engine = Engine(ThreadsExecutor(thread_pool))
    ctx = {SA_ENGINE_KEY: sa_engine}

    def execute(query_node):
        proxy = engine.execute(graph, query_node, ctx)
        return DenormalizeGraphQL(graph, proxy, "query").process(query_node)

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
    result = execute(query)
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

    engine = Engine(SyncExecutor())
    result = engine.execute(graph, query)
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

    graph = Graph([
        Node('A', [
            Field('a', String, a_fields)
        ]),
        Root([
            Link('aa', Sequence[Optional[TypeRef['A']]], lambda: [1, Nothing], requires=None)
        ])
    ])

    result = execute(
        graph,
        q.Node(
            [
                q.Link("aa", q.Node([q.Field("a")])),
            ]
        ),
    )
    assert denormalize(graph, result) == {"aa": [{"a": 42}, None]}


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

    graph = Graph([
        Node('A', [
            Field('a', String, a_fields),
            Link('b1', Sequence[Optional[TypeRef['B']]], lambda: [1, Nothing], requires=None),
            # same as 'b' but with requires
            Link('b2', Sequence[Optional[TypeRef['B']]], link_b2, requires='a'),
        ]),
        Node('B', [
            Field('b', String, b_fields)
        ]),
        Root([
            Link('a_root', TypeRef['A'], lambda: 1, requires=None)
        ])
    ])

    result = execute(
        graph,
        q.Node(
            [
                q.Link("a_root", q.Node([
                    q.Field("a"),
                    q.Link("b1", q.Node([
                        q.Field("b")
                    ])),
                    q.Link("b2", q.Node([
                        q.Field("b")
                    ])),
                ])),
            ]
        ),
    )
    assert denormalize(graph, result) == {
        "a_root": {
            "a": 42,
            "b1": [{"b": 24}, None],
            "b2": [{"b": 24}, None]
        }
    }


def test_overlapped_query_node_with_fragment():
    def resolve_user(fields, ids):
        def get_field(f, id_):
            if f.name == "name":
                return "John"
            elif f.name == "id":
                return id_

        return [[get_field(f, id_) for f in fields] for id_ in ids]

    graph = Graph([
        Node('User', [
            Field('id', String, resolve_user),
            Field('name', String, resolve_user),
        ]),
        Node('Context', [
            Link('user', TypeRef['User'], lambda: 1, requires=None)
        ]),
        Root([
            Link('context', TypeRef['Context'], lambda: 1, requires=None)
        ])
    ])

    query = """
    query GetUser {
        context {
            user {
                id
                name
            }
            ... on Context {
                user {
                    id
                }
            }
        }
    }
    """

    result = execute(graph, read(query))

    assert denormalize(graph, result) == {
        "context": {
            "user": {
                "id": 1,
                "name": "John"
            }
        }
    }
