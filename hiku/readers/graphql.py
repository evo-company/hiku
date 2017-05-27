from __future__ import absolute_import

from itertools import chain

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

    def visit_Document(self, obj):
        for definition in obj.definitions:
            self.visit(definition)

    def visit_OperationDefinition(self, obj):
        self.visit(obj.selection_set)

    def visit_FragmentDefinition(self, obj):
        self.visit(obj.selection_set)

    def visit_SelectionSet(self, obj):
        for i in obj.selections:
            self.visit(i)

    def visit_Field(self, obj):
        pass

    def visit_FragmentSpread(self, obj):
        pass

    def visit_InlineFragment(self, obj):
        self.visit(obj.selection_set)


class FragmentsCollector(NodeVisitor):

    def __init__(self):
        self.fragments_map = {}

    def visit_OperationDefinition(self, obj):
        pass  # not interested in operations here

    def visit_FragmentDefinition(self, obj):
        if obj.name.value in self.fragments_map:
            raise TypeError('Duplicated fragment name: "{}"'
                            .format(obj.name.value))
        self.fragments_map[obj.name.value] = obj


class SelectionSetVisitMixin(object):

    def transform_fragment(self, name):
        raise NotImplementedError

    @property
    def query_variables(self):
        raise NotImplementedError

    @property
    def query_name(self):
        raise NotImplementedError

    def lookup_variable(self, name):
        try:
            return self.query_variables[name]
        except KeyError:
            raise TypeError('Variable ${} is not defined in query {}'
                            .format(name, self.query_name))

    def visit_SelectionSet(self, obj):
        for i in obj.selections:
            for j in self.visit(i):
                yield j

    def visit_Field(self, obj):
        if obj.alias is not None:
            raise TypeError('Field aliases are not supported: {!r}'
                            .format(obj))
        options = {arg.name.value: self.visit(arg.value)
                   for arg in obj.arguments}
        if obj.selection_set is None:
            yield Field(obj.name.value, options or None)
        else:
            node = Node(list(self.visit(obj.selection_set)))
            yield Link(obj.name.value, node, options or None)

    def visit_Variable(self, obj):
        return self.lookup_variable(obj.name.value)

    def _visit_scalar(self, obj):
        return obj.value

    def visit_IntValue(self, obj):
        return int(obj.value)

    def visit_FloatValue(self, obj):
        return float(obj.value)

    def visit_StringValue(self, obj):
        return obj.value

    def visit_BooleanValue(self, obj):
        return obj.value

    def visit_EnumValue(self, obj):
        return obj.value

    def visit_ListValue(self, obj):
        return [self.visit(i) for i in obj.values]

    def visit_ObjectValue(self, obj):
        return {f.name.value: self.visit(f.value) for f in obj.fields}

    def visit_FragmentSpread(self, obj):
        assert not obj.directives, obj.directives
        for i in self.transform_fragment(obj.name.value):
            yield i

    def visit_InlineFragment(self, obj):
        for i in self.visit(obj.selection_set):
            yield i


class FragmentsTransformer(SelectionSetVisitMixin, NodeVisitor):
    query_name = None
    query_variables = None

    def __init__(self, document, query_name, query_variables):
        collector = FragmentsCollector()
        collector.visit(document)
        self.query_name = query_name
        self.query_variables = query_variables
        self.fragments_map = collector.fragments_map
        self.cache = {}
        self.pending_fragments = set()

    def transform_fragment(self, name):
        return self.visit(self.fragments_map[name])

    def visit_OperationDefinition(self, obj):
        pass  # not interested in operations here

    def visit_FragmentDefinition(self, obj):
        if obj.name.value in self.cache:
            return self.cache[obj.name.value]
        else:
            if obj.name.value in self.pending_fragments:
                raise TypeError('Cyclic fragment usage: "{}"'
                                .format(obj.name.value))
            self.pending_fragments.add(obj.name.value)
            try:
                selection_set = list(self.visit(obj.selection_set))
            finally:
                self.pending_fragments.discard(obj.name.value)
            self.cache[obj.name.value] = selection_set
            return selection_set


class GraphQLTransformer(SelectionSetVisitMixin, NodeVisitor):
    query_name = None
    query_variables = None
    fragments_transformer = None

    def __init__(self, document, variables=None):
        self.document = document
        self.variables = variables

    @classmethod
    def transform(cls, document, variables=None):
        visitor = cls(document, variables)
        return visitor.visit(document)

    def transform_fragment(self, name):
        return self.fragments_transformer.transform_fragment(name)

    def visit_Document(self, obj):
        queries = list(chain.from_iterable(self.visit(i)
                                           for i in obj.definitions))
        if len(queries) != 1:
            raise TypeError('Only single operation per document is '
                            'supported, {} operations was provided'
                            .format(len(obj.definitions)))
        return queries[0]

    def visit_OperationDefinition(self, obj):
        if obj.operation != 'query':
            raise TypeError('Only "query" operations are supported, '
                            '"{}" operation was provided'
                            .format(obj.operation))
        assert obj.operation == 'query', obj.operation

        variables = self.variables or {}
        query_name = obj.name.value if obj.name else '<unnamed>'
        query_variables = {}
        for var_defn in obj.variable_definitions or ():
            name = var_defn.variable.name.value
            try:
                value = variables[name]
            except KeyError:
                if var_defn.default_value is not None:
                    value = self.visit(var_defn.default_value)
                else:
                    raise TypeError('Variable "{}" is not provided for query {}'
                                    .format(name, query_name))
            query_variables[name] = value

        self.query_name = query_name
        self.query_variables = query_variables
        self.fragments_transformer = FragmentsTransformer(self.document,
                                                          self.query_name,
                                                          self.query_variables)
        try:
            node = Node(list(self.visit(obj.selection_set)))
        finally:
            self.query_name = None
            self.query_variables = None
            self.fragments_transformer = None
        yield node

    def visit_FragmentDefinition(self, obj):
        return []  # not interested in fragments here


def read(src, variables=None):
    doc = parse(src)
    return GraphQLTransformer.transform(doc, variables)
