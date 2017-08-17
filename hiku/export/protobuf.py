from google.protobuf.json_format import ParseDict

from ..query import QueryVisitor
from ..protobuf import query_pb2


class Exporter(QueryVisitor):

    def __init__(self, node):
        self.stack = [node]

    def visit_field(self, obj):
        field = self.stack[-1].items.add().field
        field.name = obj.name
        if obj.options is not None:
            ParseDict(obj.options, field.options)

    def visit_link(self, obj):
        link = self.stack[-1].items.add().link
        link.name = obj.name
        if obj.options is not None:
            ParseDict(obj.options, link.options)
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
