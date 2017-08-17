from __future__ import unicode_literals

import pytest

from google.protobuf.json_format import ParseError

from hiku.query import Field, Link, Node
from hiku.protobuf import query_pb2
from hiku.export.protobuf import export


UNKNOWN = object()


def test_node():
    node = query_pb2.Node()
    node.items.add().field.name = 'aimer'

    query = Node([Field('aimer')])

    assert export(query) == node


def test_field_options():
    node = query_pb2.Node()
    field = node.items.add().field
    field.name = 'cody'
    field.options['kink'] = 1234
    field.options['cithara'] = 'slasher'

    query = Node([Field('cody', options={'kink': 1234, 'cithara': 'slasher'})])

    assert export(query) == node


def test_link_options():
    node = query_pb2.Node()
    link = node.items.add().link
    link.name = 'pommee'
    link.options['takest'] = 3456
    link.options['decoy'] = 'nyroca'

    field = link.node.items.add().field
    field.name = 'fugazi'

    query = Node([Link('pommee', Node([Field('fugazi')]),
                       options={'takest': 3456, 'decoy': 'nyroca'})])

    assert export(query) == node


def test_invalid_options():
    with pytest.raises(ParseError) as type_err:
        export(Node([Field('kott',
                           options={'clauber': UNKNOWN})]))
    type_err.match('Unexpected type for Value message')

    with pytest.raises(ParseError) as item_type_err:
        export(Node([Field('puerco',
                           options={'bayat': [1, UNKNOWN, 3]})]))
    item_type_err.match('Unexpected type for Value message')
