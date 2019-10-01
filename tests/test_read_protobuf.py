import pytest

from hiku.query import Node, Field, Link
from hiku.protobuf import query_pb2 as t
from hiku.readers.protobuf import read, transform


def check_read(pb_node, expected):
    query = read(pb_node.SerializeToString())
    assert query == expected


def test_node_field():
    node = t.Node()
    item = node.items.add()
    item.field.name = 'tratan'
    check_read(node, Node([Field('tratan')]))


def test_node_field_options():
    node = t.Node()
    item = node.items.add()
    item.field.name = 'sprayed'
    item.field.options['treason'] = 123
    item.field.options['prizren'] = 'stager'
    check_read(node, Node([Field('sprayed', {'treason': 123,
                                             'prizren': 'stager'})]))


def test_link():
    node = t.Node()
    link_item = node.items.add()
    link_item.link.name = 'swaying'
    field_item = link_item.link.node.items.add()
    field_item.field.name = 'pelew'
    check_read(node, Node([Link('swaying', Node([Field('pelew')]))]))


def test_link_options():
    node = t.Node()
    link_item = node.items.add()
    link_item.link.name = 'dubiety'
    link_item.link.options['squat'] = 234
    link_item.link.options['liquid'] = 'ravages'
    field_item = link_item.link.node.items.add()
    field_item.field.name = 'gits'
    check_read(node, Node([Link('dubiety', Node([Field('gits')]),
                                {'squat': 234, 'liquid': 'ravages'})]))


def test_no_field_name():
    node = t.Node()
    item = node.items.add()
    item.field.CopyFrom(t.Field())
    with pytest.raises(TypeError) as err:
        transform(node)
    err.match('Field name is empty')


def test_no_link_name():
    node = t.Node()
    item = node.items.add()
    item.link.CopyFrom(t.Link())
    with pytest.raises(TypeError) as err:
        transform(node)
    err.match('Link name is empty')


def test_no_node_item():
    node = t.Node()
    node.items.add()
    with pytest.raises(TypeError) as err:
        transform(node)
    err.match('Node item is empty')
