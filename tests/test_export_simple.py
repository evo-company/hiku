from hiku.edn import dumps
from hiku.query import Field, Link, Node
from hiku.export.simple import export


def check_export(query_obj, data):
    assert dumps(export(query_obj)) == data


def test_field():
    check_export(Field('foo'), ':foo')
    check_export(Field('foo', options={'bar': 'baz'}),
                 '(:foo {:bar "baz"})')


def test_link():
    check_export(Link('foo', Node([])), '{:foo []}')
    check_export(Link('foo', Node([]), options={'bar': 'baz'}),
                 '{(:foo {:bar "baz"}) []}')


def test_node():
    check_export(Node([Field('foo')]), '[:foo]')


def test_options():
    check_export(
        Node([Field('foo', options={'bar': [1, {'baz': 2}, {3}]})]),
        '[(:foo {:bar [1 {:baz 2} #{3}]})]',
    )
