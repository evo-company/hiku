from __future__ import unicode_literals

from hiku.edn import dumps
from hiku.query import Field, Link, Edge
from hiku.export.simple import export


def check_export(node, data):
    assert dumps(export(node)) == data


def test_field():
    check_export(Field('foo'), ':foo')
    check_export(Field('foo', options={'bar': 'baz'}),
                 '(:foo {:bar "baz"})')


def test_link():
    check_export(Link('foo', Edge([])), '{:foo []}')
    check_export(Link('foo', Edge([]), options={'bar': 'baz'}),
                 '{(:foo {:bar "baz"}) []}')


def test_edge():
    check_export(Edge([Field('foo')]), '[:foo]')
