from hiku.query import merge, Node, Field, Link


def test():
    query = merge(
        [
            Node(
                [
                    Field("a1"),
                    Field("a1"),
                    Field("a2"),
                    Field("a2"),
                    Link(
                        "b",
                        Node(
                            [
                                Field("b1"),
                                Field("b2"),
                            ]
                        ),
                        options={"x": 1},
                    ),
                ]
            ),
            Node(
                [
                    Field("a2"),
                    Field("a2"),
                    Field("a3"),
                    Field("a3"),
                    Link(
                        "b",
                        Node(
                            [
                                Field("b2"),
                                Field("b3"),
                            ]
                        ),
                        options={"x": 1},
                    ),
                ]
            ),
        ]
    )
    expected = Node(
        [
            Field("a1"),
            Field("a2"),
            Field("a3"),
            Link(
                "b",
                Node(
                    [
                        Field("b1"),
                        Field("b2"),
                        Field("b3"),
                    ]
                ),
                options={"x": 1},
            ),
        ]
    )
    assert query == expected


def test_alias():
    query = merge(
        [
            Node(
                [
                    Field("a", alias="a1"),
                    Field("a", alias="a2"),
                    Link("b", Node([Field("c")]), alias="b1"),
                    Link("b", Node([Field("c")]), alias="b2"),
                ]
            ),
        ]
    )
    assert query == Node(
        [
            Field("a", alias="a1"),
            Field("a", alias="a2"),
            Link("b", Node([Field("c")]), alias="b1"),
            Link("b", Node([Field("c")]), alias="b2"),
        ]
    )


def test_distinct_by_options_fields():
    query = Node(
        [
            Field("a"),
            Field("a", options={"x": 1}),
            Field("a"),
        ]
    )
    assert merge([query]) == Node(
        [
            Field("a"),
            Field("a", options={"x": 1}),
        ]
    )


def test_distinct_by_name_fields():
    query = Node(
        [
            Field("a"),
            Field("b", options={"x": 1}, alias="a"),
            Field("a"),
        ]
    )
    assert merge([query]) == Node(
        [
            Field("a"),
            Field("b", options={"x": 1}, alias="a"),
        ]
    )


def test_distinct_by_options_links():
    query = Node(
        [
            Link("a", Node([Field("c")])),
            Link("a", Node([Field("d")]), options={"x": 1}),
            Link("a", Node([Field("e")])),
        ]
    )
    assert merge([query]) == Node(
        [
            Link("a", Node([Field("c"), Field("e")])),
            Link("a", Node([Field("d")]), options={"x": 1}),
        ]
    )


def test_distinct_by_name_links():
    query = Node(
        [
            Link("a", Node([Field("c")])),
            Link("b", Node([Field("d")]), options={"x": 1}, alias="a"),
            Link("a", Node([Field("e")])),
        ]
    )
    assert merge([query]) == Node(
        [
            Link("a", Node([Field("c"), Field("e")])),
            Link("b", Node([Field("d")]), options={"x": 1}, alias="a"),
        ]
    )
