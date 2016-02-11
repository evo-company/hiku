from __future__ import absolute_import

from graphql.core.language.parser import parse
from graphql.core.language.visitor import Visitor, visit

from ..query import Edge, Field


class GraphQLTransformer(Visitor):

    def __init__(self):
        self._stack = [Edge([])]

    @classmethod
    def transform(cls, document):
        visitor = cls()
        visit(document, visitor)
        return visitor._stack[0]

    def enter_SelectionSet(self, node, key, parent, path, ancestors):
        for field in node.selections:
            self._stack[-1].fields[field.name.value] = Field(field.name.value)


def read(src):
    doc = parse(src)
    return GraphQLTransformer.transform(doc)
