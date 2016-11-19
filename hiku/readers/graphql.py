from __future__ import absolute_import

from graphql.language import ast
from graphql.language.parser import parse

from ..query import Node, Field, Link


class NodeVisitor(object):

    def visit(self, obj):
        if not isinstance(obj, ast.Node):
            raise TypeError('Unknown node type: {!r}'.format(obj))
        visit_method = getattr(self, 'visit_{}'.format(obj.__class__.__name__),
                               None)
        if visit_method is None:
            raise NotImplementedError('Not implemented node type: {!r}'
                                      .format(obj))
        return visit_method(obj)


class GraphQLTransformer(NodeVisitor):

    @classmethod
    def transform(cls, document):
        visitor = cls()
        return visitor.visit(document)

    def visit_Document(self, obj):
        if len(obj.definitions) != 1:
            raise NotImplementedError('Only single operation per document is '
                                      'supported, {} operations was provided'
                                      .format(len(obj.definitions)))
        return self.visit(obj.definitions[0])

    def visit_OperationDefinition(self, obj):
        if obj.operation != 'query':
            raise NotImplementedError('Only "query" operations are supported, '
                                      '"{}" operation was provided'
                                      .format(obj.operation))
        assert obj.operation == 'query', obj.operation
        return self.visit(obj.selection_set)

    def visit_SelectionSet(self, obj):
        return Node([self.visit(i) for i in obj.selections])

    def visit_Field(self, obj):
        if obj.alias is not None:
            raise NotImplementedError('Field aliases are not supported: {!r}'
                                      .format(obj))
        options = {arg.name.value: arg.value.value for arg in obj.arguments}
        if obj.selection_set is None:
            return Field(obj.name.value, options or None)
        else:
            node = self.visit(obj.selection_set)
            return Link(obj.name.value, node, options or None)


def read(src):
    doc = parse(src)
    return GraphQLTransformer.transform(doc)
