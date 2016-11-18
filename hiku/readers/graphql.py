from __future__ import absolute_import

from graphql.language.parser import parse
from graphql.language.visitor import Visitor, visit

from ..query import Node, Field


class GraphQLTransformer(Visitor):

    def __init__(self):
        self._stack = [set()]

    @classmethod
    def transform(cls, document):
        visitor = cls()
        visit(document, visitor)
        node = Node([Field(name) for name in visitor._stack[0]])
        return node

    def enter_SelectionSet(self, node, key, parent, path, ancestors):
        for field in node.selections:
            self._stack[-1].add(field.name.value)


def read(src):
    doc = parse(src)
    return GraphQLTransformer.transform(doc)
