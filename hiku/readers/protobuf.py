"""
    hiku.readers.protobuf
    ~~~~~~~~~~~~~~~~~~~~~

    Support for queries encoded using Protocol Buffers

"""
from google.protobuf.json_format import MessageToDict

from ..query import Node, Link, Field, merge
from ..protobuf import query_pb2


def _transform(pb_node):
    fields = []
    for i in pb_node.items:
        item_type = i.WhichOneof('value')
        if item_type == 'field':
            if not i.field.name:
                raise TypeError('Field name is empty: {!r}'.format(i))
            options = None
            if i.field.HasField('options'):
                options = MessageToDict(i.field.options)
            fields.append(Field(i.field.name, options))
        elif item_type == 'link':
            if not i.link.name:
                raise TypeError('Link name is empty: {!r}'.format(i))
            options = None
            if i.link.HasField('options'):
                options = MessageToDict(i.link.options)
            fields.append(Link(i.link.name, _transform(i.link.node), options))
        else:
            raise TypeError('Node item is empty: {!r}'.format(i))
    return Node(fields)


def transform(pb_node):
    return merge([_transform(pb_node)])


def read(data):
    """Reads a query, encoded into binary Protocol Buffers format, using
    message types from the ``hiku.protobuf.query`` package.

    Proto-file location: ``hiku/protobuf/query.proto``

    Generated message types: ``hiku.protobuf.query_pb2``

    Example:

    .. code-block:: python

        from hiku.builder import Q, build
        from hiku.export.protobuf import export

        bin_query = export(build([
            Q.characters(limit=100)[
                Q.name,
            ],
        ])).SerializeToString()

        assert bin_query == (
            b'\\n(\\x12&\\n\\ncharacters\\x12\\n\\n\\x08\\n\\x06\\n\\x04'
            b'name\\x1a\\x0c\\n\\x05limit\\x12\\x03\\x10\\xc8\\x01'
        )

        query = read(bin_query)  # reading binary message

        result = engine.execute(graph, query)

    :param bytes data: binary message representation
    :return: :py:class:`hiku.query.Node`, ready to execute query object
    """
    pb_value = query_pb2.Node.FromString(data)
    return transform(pb_value)
