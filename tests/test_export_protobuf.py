from __future__ import unicode_literals

import pytest

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
    field.options['kink'].integer = 1234
    field.options['cithara'].string = 'slasher'
    field.options['guido'].repeated_integer.items[:] = [2345, 3456]
    field.options['preterm'].repeated_string.items[:] = ['phobic', 'tunicle']

    query = Node([Field('cody', options={'kink': 1234,
                                         'cithara': 'slasher',
                                         'guido': [2345, 3456],
                                         'preterm': ['phobic', 'tunicle']})])

    assert export(query) == node


def test_link_options():
    node = query_pb2.Node()
    link = node.items.add().link
    link.name = 'pommee'
    link.options['takest'].integer = 3456
    link.options['decoy'].string = 'nyroca'

    field = link.node.items.add().field
    field.name = 'fugazi'

    query = Node([Link('pommee', Node([Field('fugazi')]),
                       options={'takest': 3456, 'decoy': 'nyroca'})])

    assert export(query) == node


def test_invalid_options():
    with pytest.raises(TypeError) as type_err:
        export(Node([Field('kott',
                           options={'clauber': UNKNOWN})]))
    type_err.match('Invalid option value type')

    with pytest.raises(TypeError) as item_type_err:
        export(Node([Field('puerco',
                           options={'bayat': [1, UNKNOWN, 3]})]))
    item_type_err.match('Invalid option items type')
