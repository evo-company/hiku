import pytest

from hiku import query as q
from hiku.graph import Graph, Node, Field, Link, Option, Root
from hiku.types import Integer, Record, Sequence, Optional, TypeRef, Boolean
from hiku.types import String, Mapping, Any
from hiku.validate.query import QueryComplexityValidator, QueryDepthValidator, validate


def _():
    return 1 / 0


class Invalid:
    def __repr__(self):
        return "<invalid>"


TYPES = {
    "Val": Record[{"attr": Integer}],
}


GRAPH = Graph(
    [
        Node("hooted", []),
        Root(
            [
                # simple
                Field("robby", None, _),
                # complex
                Field("wounded", Optional[Record[{"attr": Integer}]], _),
                Field("annuals", Record[{"attr": Integer}], _),
                Field("hialeah", Sequence[Record[{"attr": Integer}]], _),
                Field("val", Optional[TypeRef["Val"]], _),
                # nested records
                Field(
                    "rlyeh", Record[{"cthulhu": Record[{"fhtagn": Integer}]}], _
                ),
                # with options
                Field("motown", None, _, options=[Option("prine", None)]),
                Field(
                    "nyerere",
                    None,
                    _,
                    options=[Option("epaule", None, default=1)],
                ),
                Field("wreche", None, _, options=[Option("cierra", Integer)]),
                Field(
                    "hunter",
                    None,
                    _,
                    options=[Option("fried", Integer, default=1)],
                ),
                Field(
                    "tapioca",
                    None,
                    _,
                    options=[Option("arbour", Optional[Integer], default=None)],
                ),
                # simple
                Link("amyls", Sequence[TypeRef["hooted"]], _, requires=None),
                # with options
                Link(
                    "ferrous",
                    Sequence[TypeRef["hooted"]],
                    _,
                    requires=None,
                    options=[Option("cantab", None)],
                ),
                Link(
                    "knesset",
                    Sequence[TypeRef["hooted"]],
                    _,
                    requires=None,
                    options=[Option("ceases", None, default=1)],
                ),
                Link(
                    "pouria",
                    Sequence[TypeRef["hooted"]],
                    _,
                    requires=None,
                    options=[Option("flunk", Integer)],
                ),
                Link(
                    "secants",
                    Sequence[TypeRef["hooted"]],
                    _,
                    requires=None,
                    options=[Option("monadic", Integer, default=1)],
                ),
                Link(
                    "hackled",
                    Sequence[TypeRef["hooted"]],
                    _,
                    requires=None,
                    options=[Option("lawing", Optional[Integer], default=None)],
                ),
            ]
        ),
    ],
    TYPES,
)


def check_errors(query, errors):
    assert validate(GRAPH, query) == errors


def check_option_errors(options, query_options, errors):
    graph = Graph([Root([Field("glinty", None, _, options=options)])])
    query = q.Node([q.Field("glinty", options=query_options)])
    assert validate(graph, query) == [
        e.format(field="root.glinty") for e in errors
    ]


def test_field():
    # field in the root node
    check_errors(
        q.Node([q.Field("invalid")]),
        [
            'Field "invalid" is not implemented in the "root" node',
        ],
    )
    # field in the linked node
    check_errors(
        q.Node([q.Link("amyls", q.Node([q.Field("invalid")]))]),
        [
            'Field "invalid" is not implemented in the "hooted" node',
        ],
    )
    # simple field as node
    check_errors(
        q.Node([q.Link("robby", q.Node([]))]),
        [
            'Trying to query "root.robby" simple field as node',
        ],
    )


@pytest.mark.parametrize("field_name", ["wounded", "annuals", "hialeah", "val"])
def test_field_complex(field_name):
    check_errors(q.Node([q.Link(field_name, q.Node([]))]), [])
    check_errors(
        q.Node([q.Link(field_name, q.Node([q.Field("invalid")]))]),
        [
            'Unknown field name "invalid"',
        ],
    )
    check_errors(q.Node([q.Link(field_name, q.Node([q.Field("attr")]))]), [])


def test_field_complex_with_typename():
    check_errors(
        q.Node([
            q.Link('val', q.Node([q.Field('__typename'), q.Field('attr')], []))
        ]), []
    )


def test_nested_records():
    query = q.Node(
        [
            q.Link(
                "rlyeh",
                q.Node([q.Link("cthulhu", q.Node([q.Field("fhtagn")]))]),
            )
        ]
    )
    check_errors(query, [])

    query = q.Node([q.Link("rlyeh", q.Node([q.Field("cthulhu")]))])
    check_errors(query, ['Trying to query "cthulhu" link as it was a field'])

    query = q.Node(
        [
            q.Link(
                "rlyeh",
                q.Node(
                    [
                        q.Link(
                            "cthulhu",
                            q.Node(
                                [q.Link("fhtagn", q.Node([q.Field("error")]))]
                            ),
                        )
                    ]
                ),
            )
        ]
    )
    check_errors(query, ['"fhtagn" is not a link'])


def test_non_field():
    check_errors(
        q.Node([q.Field("amyls")]),
        [
            'Trying to query "root.amyls" link as it was a field',
        ],
    )


def test_field_options():
    def mk(field_name, **kwargs):
        return q.Node([q.Field(field_name, **kwargs)])

    check_errors(
        mk("motown"),
        [
            'Required option "root.motown:prine" is not specified',
        ],
    )
    check_errors(
        mk("motown", options={}),
        [
            'Required option "root.motown:prine" is not specified',
        ],
    )
    check_errors(mk("motown", options={"prine": 1}), [])
    check_errors(mk("motown", options={"prine": "1"}), [])
    check_errors(
        mk("motown", options={"prine": 1, "invalid": 1}),
        [
            'Unknown options for "root.motown": invalid',
        ],
    )

    check_errors(mk("nyerere"), [])
    check_errors(mk("nyerere", options={}), [])
    check_errors(mk("nyerere", options={"epaule": 1}), [])
    check_errors(mk("nyerere", options={"epaule": "1"}), [])
    check_errors(
        mk("nyerere", options={"epaule": 1, "invalid": 1}),
        [
            'Unknown options for "root.nyerere": invalid',
        ],
    )

    check_errors(
        mk("wreche"),
        [
            'Required option "root.wreche:cierra" is not specified',
        ],
    )
    check_errors(
        mk("wreche", options={}),
        [
            'Required option "root.wreche:cierra" is not specified',
        ],
    )
    check_errors(mk("wreche", options={"cierra": 1}), [])
    check_errors(
        mk("wreche", options={"cierra": "1"}),
        [
            'Invalid value for option "root.wreche:cierra", '
            '"str" instead of Integer',
        ],
    )
    check_errors(
        mk("wreche", options={"cierra": 1, "invalid": 1}),
        [
            'Unknown options for "root.wreche": invalid',
        ],
    )

    check_errors(mk("hunter"), [])
    check_errors(mk("hunter", options={}), [])
    check_errors(mk("hunter", options={"fried": 1}), [])
    check_errors(
        mk("hunter", options={"fried": "1"}),
        [
            'Invalid value for option "root.hunter:fried", '
            '"str" instead of Integer',
        ],
    )
    check_errors(
        mk("hunter", options={"fried": 1, "invalid": 1}),
        [
            'Unknown options for "root.hunter": invalid',
        ],
    )

    check_errors(mk("tapioca"), [])
    check_errors(mk("tapioca", options={}), [])
    check_errors(mk("tapioca", options={"arbour": None}), [])
    check_errors(mk("tapioca", options={"arbour": 123}), [])
    check_errors(
        mk("tapioca", options={"arbour": "123"}),
        [
            'Invalid value for option "root.tapioca:arbour", '
            '"str" instead of Integer',
        ],
    )


def test_link():
    lnk = q.Link("invalid", q.Node([]))
    # link in the root node
    check_errors(
        q.Node([lnk]),
        [
            'Link "invalid" is not implemented in the "root" node',
        ],
    )
    # link in the linked node
    check_errors(
        q.Node([q.Link("amyls", q.Node([lnk]))]),
        [
            'Link "invalid" is not implemented in the "hooted" node',
        ],
    )


def test_link_options():
    def mk(link_name, **kwargs):
        return q.Node([q.Link(link_name, q.Node([]), **kwargs)])

    check_errors(
        mk("ferrous"),
        [
            'Required option "root.ferrous:cantab" is not specified',
        ],
    )
    check_errors(
        mk("ferrous", options={}),
        [
            'Required option "root.ferrous:cantab" is not specified',
        ],
    )
    check_errors(mk("ferrous", options={"cantab": 1}), [])
    check_errors(mk("ferrous", options={"cantab": "1"}), [])
    check_errors(
        mk("ferrous", options={"cantab": 1, "invalid": 1}),
        [
            'Unknown options for "root.ferrous": invalid',
        ],
    )

    check_errors(mk("knesset"), [])
    check_errors(mk("knesset", options={}), [])
    check_errors(mk("knesset", options={"ceases": 1}), [])
    check_errors(mk("knesset", options={"ceases": "1"}), [])
    check_errors(
        mk("knesset", options={"ceases": 1, "invalid": 1}),
        [
            'Unknown options for "root.knesset": invalid',
        ],
    )

    check_errors(
        mk("pouria"),
        [
            'Required option "root.pouria:flunk" is not specified',
        ],
    )
    check_errors(
        mk("pouria", options={}),
        [
            'Required option "root.pouria:flunk" is not specified',
        ],
    )
    check_errors(mk("pouria", options={"flunk": 1}), [])
    check_errors(
        mk("pouria", options={"flunk": "1"}),
        [
            'Invalid value for option "root.pouria:flunk", '
            '"str" instead of Integer',
        ],
    )
    check_errors(
        mk("pouria", options={"flunk": 1, "invalid": 1}),
        [
            'Unknown options for "root.pouria": invalid',
        ],
    )

    check_errors(mk("secants"), [])
    check_errors(mk("secants", options={}), [])
    check_errors(mk("secants", options={"monadic": 1}), [])
    check_errors(
        mk("secants", options={"monadic": "1"}),
        [
            'Invalid value for option "root.secants:monadic", '
            '"str" instead of Integer',
        ],
    )
    check_errors(
        mk("secants", options={"monadic": 1, "invalid": 1}),
        [
            'Unknown options for "root.secants": invalid',
        ],
    )

    check_errors(mk("hackled", options={}), [])
    check_errors(mk("hackled", options={"lawing": None}), [])
    check_errors(mk("hackled", options={"lawing": 123}), [])
    check_errors(
        mk("hackled", options={"lawing": "123"}),
        [
            'Invalid value for option "root.hackled:lawing", '
            '"str" instead of Integer',
        ],
    )


def test_missing_options():
    check_option_errors(
        [Option("lawing", Integer)],
        {},
        ['Required option "{field}:lawing" is not specified'],
    )
    check_option_errors(
        [Option("lawing", Integer, default=1)],
        {},
        [],
    )
    check_option_errors(
        [Option("lawing", Optional[Integer])],
        {},
        ['Required option "{field}:lawing" is not specified'],
    )
    check_option_errors(
        [Option("lawing", Optional[Integer], default=None)],
        {},
        [],
    )


def test_scalar_option_type_errors():
    check_option_errors([Option("lawing", Boolean)], {"lawing": True}, [])
    check_option_errors(
        [Option("lawing", Boolean)],
        {"lawing": Invalid()},
        [
            'Invalid value for option "{field}:lawing", '
            '"Invalid" instead of Boolean'
        ],
    )
    check_option_errors([Option("lawing", Integer)], {"lawing": 123}, [])
    check_option_errors(
        [Option("lawing", Integer)],
        {"lawing": Invalid()},
        [
            'Invalid value for option "{field}:lawing", '
            '"Invalid" instead of Integer'
        ],
    )
    check_option_errors([Option("lawing", String)], {"lawing": "raundon"}, [])
    check_option_errors(
        [Option("lawing", String)],
        {"lawing": Invalid()},
        [
            'Invalid value for option "{field}:lawing", '
            '"Invalid" instead of String'
        ],
    )


def test_optional_option_type_errors():
    check_option_errors(
        [Option("lawing", Optional[Integer])],
        {"lawing": None},
        [],
    )
    check_option_errors(
        [Option("lawing", Optional[Integer])],
        {"lawing": Invalid()},
        [
            'Invalid value for option "{field}:lawing", '
            '"Invalid" instead of Integer'
        ],
    )


def test_sequence_option_type_errors():
    check_option_errors(
        [Option("lawing", Sequence[Integer])],
        {"lawing": [123]},
        [],
    )
    check_option_errors(
        [Option("lawing", Sequence[Integer])],
        {"lawing": Invalid()},
        [
            'Invalid value for option "{field}:lawing", '
            '"Invalid" instead of Sequence[Integer]'
        ],
    )
    check_option_errors(
        [Option("lawing", Sequence[Integer])],
        {"lawing": [Invalid()]},
        [
            'Invalid value for option "{field}:lawing", '
            '"Invalid" instead of Integer'
        ],
    )


def test_mapping_option_type_errors():
    check_option_errors(
        [Option("lawing", Mapping[Integer, String])],
        {"lawing": {123: "oik"}},
        [],
    )
    check_option_errors(
        [Option("lawing", Mapping[Integer, String])],
        {"lawing": Invalid()},
        [
            'Invalid value for option "{field}:lawing", '
            '"Invalid" instead of Mapping[Integer, String]'
        ],
    )
    check_option_errors(
        [Option("lawing", Mapping[Integer, String])],
        {"lawing": {Invalid(): "oik"}},
        [
            'Invalid value for option "{field}:lawing", '
            '"Invalid" instead of Integer'
        ],
    )
    check_option_errors(
        [Option("lawing", Mapping[Integer, String])],
        {"lawing": {123: Invalid()}},
        [
            'Invalid value for option "{field}:lawing", '
            '"Invalid" instead of String'
        ],
    )


def test_record_option_type_errors():
    check_option_errors(
        [Option("lawing", Record[{"tingent": Integer}])],
        {"lawing": {"tingent": 123}},
        [],
    )
    check_option_errors(
        [Option("lawing", Record[{"tingent": Integer}])],
        {"lawing": Invalid()},
        [
            'Invalid value for option "{field}:lawing", '
            "\"Invalid\" instead of Record[{{'tingent': Integer}}]"
        ],
    )
    check_option_errors(
        [Option("lawing", Record[{"tingent": Integer}])],
        {"lawing": {}},
        [
            'Invalid value for option "{field}:lawing", '
            "missing fields: tingent"
        ],
    )
    check_option_errors(
        [Option("lawing", Record[{"tingent": Integer}])],
        {"lawing": {Invalid(): 1}},
        [
            'Invalid value for option "{field}:lawing", '
            "unknown fields: <invalid>"
        ],
    )
    check_option_errors(
        [Option("lawing", Record[{"tingent": Integer}])],
        {"lawing": {"tingent": Invalid()}},
        [
            'Invalid value for option "{field}:lawing", '
            '"Invalid" instead of Integer'
        ],
    )


def test_distinct_by_name_fields():
    graph = Graph(
        [
            Node(
                "X",
                [
                    Field("a", None, None),
                    Field("b", None, None),
                ],
            ),
            Root(
                [
                    Link("x", TypeRef["X"], None, requires=None),
                ]
            ),
        ]
    )
    errors = validate(
        graph,
        q.Node(
            [
                q.Link(
                    "x",
                    q.Node(
                        [
                            q.Field("a"),
                            q.Field("b", alias="a"),
                        ]
                    ),
                ),
            ]
        ),
    )
    assert errors == [
        'Found distinct fields with the same resulting name "a" for the '
        'node "X"',
    ]


def test_distinct_by_options_fields():
    graph = Graph(
        [
            Node(
                "X",
                [
                    Field(
                        "a",
                        None,
                        None,
                        options=[Option("e", Optional[Integer], default=None)],
                    ),
                ],
            ),
            Root(
                [
                    Link("x", TypeRef["X"], None, requires=None),
                ]
            ),
        ]
    )
    errors = validate(
        graph,
        q.Node(
            [
                q.Link(
                    "x",
                    q.Node(
                        [
                            q.Field("a"),
                            q.Field("a", options={"e": 1}),
                        ]
                    ),
                ),
            ]
        ),
    )
    assert errors == [
        'Found distinct fields with the same resulting name "a" for the '
        'node "X"',
    ]


def test_distinct_by_name_links():
    graph = Graph(
        [
            Node(
                "X",
                [
                    Field("a", None, None),
                ],
            ),
            Root(
                [
                    Link("x1", TypeRef["X"], None, requires=None),
                    Link("x2", TypeRef["X"], None, requires=None),
                ]
            ),
        ]
    )
    errors = validate(
        graph,
        q.Node(
            [
                q.Link("x1", q.Node([q.Field("a")])),
                q.Link("x2", q.Node([q.Field("a")]), alias="x1"),
            ]
        ),
    )
    assert errors == [
        'Found distinct fields with the same resulting name "x1" for the '
        'node "root"'
    ]


def test_distinct_by_options_links():
    graph = Graph(
        [
            Node(
                "X",
                [
                    Field("a", None, None),
                ],
            ),
            Root(
                [
                    Link(
                        "x",
                        TypeRef["X"],
                        None,
                        requires=None,
                        options=[Option("e", Optional[Integer], default=None)],
                    ),
                ]
            ),
        ]
    )
    errors = validate(
        graph,
        q.Node(
            [
                q.Link("x", q.Node([q.Field("a")])),
                q.Link("x", q.Node([q.Field("a")]), options={"e": 1}),
            ]
        ),
    )
    assert errors == [
        'Found distinct fields with the same resulting name "x" for the '
        'node "root"'
    ]


def test_typeref_in_option():
    data_types = {
        "Foo": Record[
            {
                "key": Integer,
            }
        ],
    }
    graph = Graph(
        [
            Root(
                [
                    Field(
                        "get",
                        None,
                        None,
                        options=[Option("foo", TypeRef["Foo"])],
                    ),
                ]
            ),
        ],
        data_types=data_types,
    )
    assert (
        validate(
            graph,
            q.Node(
                [
                    q.Field("get", options={"foo": {"key": 1}}),
                ]
            ),
        )
        == []
    )
    assert validate(
        graph,
        q.Node(
            [
                q.Field("get", options={"foo": {"key": "1"}}),
            ]
        ),
    ) == ['Invalid value for option "root.get:foo", "str" instead of Integer']


def test_any_in_option():
    graph = Graph(
        [
            Root(
                [
                    Field(
                        "get",
                        None,
                        None,
                        options=[
                            Option("foo", Mapping[String, Any]),
                        ],
                    ),
                ]
            ),
        ]
    )
    assert (
        validate(
            graph,
            q.Node(
                [
                    q.Field("get", options={"foo": {"key": 1}}),
                ]
            ),
        )
        == []
    )
    assert validate(
        graph,
        q.Node(
            [
                q.Field("get", options={"foo": "bar"}),
            ]
        ),
    ) == [
        'Invalid value for option "root.get:foo", '
        '"str" instead of Mapping[String, Any]'
    ]


# TODO test complex field
# TODO test with options
# TODO: test with records
# TODO: test with fragments
# TODO: research about query complexity techniques
def test_query_complexity_validator():
    validator = QueryComplexityValidator()

    query = q.Node([
        q.Field("a"),
        q.Field("b"),
        q.Link("c", q.Node([
            q.Field("d"),
            q.Field("e"),
        ])),
    ])

    assert validator.validate(query) == 5


def test_query_depth_validator():
    validator = QueryDepthValidator()

    query = q.Node([
        q.Field("a"),
        q.Field("b"),
        q.Link("c", q.Node([
            q.Field("d"),
            q.Field("e"),
        ])),
    ])

    assert validator.validate(query) == 3
