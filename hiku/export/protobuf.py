from ..query import QueryVisitor
from ..compat import string_types
from ..protobuf import query_pb2


class Exporter(QueryVisitor):

    def __init__(self, node):
        self.stack = [node]

    def _populate_options(self, pb_obj, options):
        for k, v in options.items():
            if isinstance(v, int):
                pb_obj.options[k].integer = v
            elif isinstance(v, string_types):
                pb_obj.options[k].string = v
            else:
                raise TypeError('Invalid option value type: {}={!r}'
                                .format(k, v))

    def visit_field(self, obj):
        field = self.stack[-1].items.add().field
        field.name = obj.name
        if obj.options is not None:
            self._populate_options(field, obj.options)

    def visit_link(self, obj):
        link = self.stack[-1].items.add().link
        link.name = obj.name
        if obj.options is not None:
            self._populate_options(link, obj.options)
        self.stack.append(link.node)
        try:
            self.visit(obj.node)
        finally:
            self.stack.pop()

    def visit_node(self, obj):
        for item in obj.fields:
            self.visit(item)


def export(query):
    node = query_pb2.Node()
    Exporter(node).visit(query)
    return node
