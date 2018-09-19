import pytest

from hiku.query import merge, Node, Field, Link


def test():
    query = merge([
        Node([
            Field('a1'),
            Field('a2'),
            Link('b', Node([
                Field('b1'),
                Field('b2'),
            ]), options={'x': 1}),
        ]),
        Node([
            Field('a2'),
            Field('a3'),
            Link('b', Node([
                Field('b2'),
                Field('b3'),
            ]), options={'x': 1}),
        ]),
    ])
    expected = Node([
        Field('a1'),
        Field('a2'),
        Field('a3'),
        Link('b', Node([
            Field('b1'),
            Field('b2'),
            Field('b3'),
        ]), options={'x': 1}),
    ])
    assert query == expected


def test_alias():
    query = merge([
        Node([
            Field('a', alias='a1'),
            Field('a', alias='a2'),
            Link('b', Node([Field('c')]), alias='b1'),
            Link('b', Node([Field('c')]), alias='b2'),
        ]),
    ])
    assert query == Node([
        Field('a', alias='a1'),
        Field('a', alias='a2'),
        Link('b', Node([Field('c')]), alias='b1'),
        Link('b', Node([Field('c')]), alias='b2'),
    ])


def test_distinct_fields():
    with pytest.raises(ValueError) as e1:
        merge([
            Node([
                Field('a'),
                Field('a', options={'x': 1}),
            ]),
        ])
    e1.match('Found distinct fields with the same resulting name')

    with pytest.raises(ValueError) as e2:
        merge([
            Node([
                Field('a'),
                Field('b', options={'x': 1}, alias='a'),
            ]),
        ])
    e2.match('Found distinct fields with the same resulting name')


def test_distinct_links():
    with pytest.raises(ValueError) as e1:
        merge([
            Node([
                Link('a', Node([Field('c')])),
                Link('a', Node([Field('d')]), options={'x': 1}),
            ]),
        ])
    e1.match('Found distinct links with the same resulting name')

    with pytest.raises(ValueError) as e2:
        merge([
            Node([
                Link('a', Node([Field('c')])),
                Link('b', Node([Field('d')]), options={'x': 1}, alias='a'),
            ]),
        ])
    e2.match('Found distinct links with the same resulting name')
