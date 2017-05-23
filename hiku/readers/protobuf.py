from ..query import Node, Link, Field
from ..protobuf import query_pb2


_OPTION_VALUE_GETTERS = {
    'string': lambda op: op.string,
    'integer': lambda op: op.integer,
    'repeated_string': lambda op: list(op.repeated_string.items),
    'repeated_integer': lambda op: list(op.repeated_integer.items),
}


def _transform_options(pb_obj):
    options = {}
    for key, pb_option in pb_obj.options.items():
        option_type = pb_option.WhichOneof('value')
        if option_type is None:
            raise TypeError('Option value is not set: {!r}'.format(pb_option))
        options[key] = _OPTION_VALUE_GETTERS[option_type](pb_option)
    return options or None


def transform(pb_node):
    fields = []
    for i in pb_node.items:
        item_type = i.WhichOneof('value')
        if item_type == 'field':
            if not i.field.name:
                raise TypeError('Field name is empty: {!r}'.format(i))
            fields.append(Field(i.field.name, _transform_options(i.field)))
        elif item_type == 'link':
            if not i.link.name:
                raise TypeError('Link name is empty: {!r}'.format(i))
            fields.append(Link(i.link.name, transform(i.link.node),
                               _transform_options(i.link)))
        else:
            raise TypeError('Node item is empty: {!r}'.format(i))
    return Node(fields)


def read(data):
    pb_value = query_pb2.Node.FromString(data)
    return transform(pb_value)
