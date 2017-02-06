from ..query import Node, Link, Field
from ..protobuf import query_pb2


def _transform_options(pb_obj):
    options = {}
    for key, pb_option in pb_obj.options.items():
        option_type = pb_option.WhichOneof('value')
        assert option_type, 'Option value is not set: {!r}'.format(pb_option)
        options[key] = getattr(pb_option, option_type)
    return options or None


def transform(pb_node):
    fields = []
    for f in pb_node.fields:
        assert f.name, f
        fields.append(Field(f.name, _transform_options(f)))
    for l in pb_node.links:
        assert l.name and l.node, l
        fields.append(Link(l.name, transform(l.node), _transform_options(l)))
    return Node(fields)


def read(data):
    pb_value = query_pb2.Node.FromString(data)
    return transform(pb_value)
