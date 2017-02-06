from __future__ import unicode_literals

from hiku.query import Node, Field, Link
from hiku.protobuf import query_pb2 as t
from hiku.readers.protobuf import read

from .base import reqs_eq_patcher


def check_read(pb_node, expected):
    query = read(pb_node.SerializeToString())
    with reqs_eq_patcher():
        assert query == expected


def test_node_field():
    field = t.Field()
    field.name = 'tratan'

    node = t.Node()
    node.fields.extend([field])

    check_read(node, Node([Field('tratan')]))


def test_node_field_options():
    field = t.Field()
    field.name = 'sprayed'
    field.options['treason'].integer = 123
    field.options['prizren'].string = 'stager'

    node = t.Node()
    node.fields.extend([field])

    check_read(node, Node([Field('sprayed', {'treason': 123,
                                             'prizren': 'stager'})]))


def test_link():
    field = t.Field()
    field.name = 'pelew'

    link = t.Link()
    link.name = 'swaying'
    link.node.fields.extend([field])

    node = t.Node()
    node.links.extend([link])

    check_read(node, Node([Link('swaying', Node([Field('pelew')]))]))


def test_link_options():
    field = t.Field()
    field.name = 'gits'

    link = t.Link()
    link.name = 'dubiety'
    link.node.fields.extend([field])
    link.options['squat'].integer = 234
    link.options['liquid'].string = 'ravages'

    node = t.Node()
    node.links.extend([link])

    check_read(node, Node([Link('dubiety', Node([Field('gits')]),
                                {'squat': 234,
                                 'liquid': 'ravages'})]))
