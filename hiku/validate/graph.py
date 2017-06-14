from itertools import chain
from contextlib import contextmanager
from collections import Counter

from ..graph import GraphVisitor, Root
from ..graph import AbstractNode, AbstractField, AbstractLink, AbstractOption

from .errors import Errors


class GraphValidationError(TypeError):

    def __init__(self, errors):
        self.errors = errors
        errors_list = '\n'.join('- {}'.format(e) for e in errors)
        super(GraphValidationError, self).__init__('\n' + errors_list)


class GraphValidator(GraphVisitor):

    class _NameFormatter(GraphVisitor):

        def visit_node(self, obj):
            return obj.name

        def visit_root(self, obj):
            return 'root'

        def visit_link(self, obj):
            return '.{}'.format(obj.name)

        def visit_field(self, obj):
            return '.{}'.format(obj.name)

        def visit_option(self, obj):
            return ':{}'.format(obj.name)

    _name_formatter = _NameFormatter()
    _graph_accept_types = (AbstractNode,)
    _node_accept_types = (AbstractNode, AbstractField, AbstractLink)
    _link_accept_types = (AbstractOption,)

    def __init__(self, items):
        self.items = items
        self.errors = Errors()
        self._ctx = []

    @classmethod
    def validate(cls, items):
        validator = cls(items)
        validator.visit_graph_items(items)
        if validator.errors.list:
            raise GraphValidationError(validator.errors.list)

    @contextmanager
    def push_ctx(self, obj):
        self._ctx.append(obj)
        try:
            yield
        finally:
            self._ctx.pop()

    @property
    def ctx(self):
        return self._ctx[-1]

    def _get_duplicates(self, names):
        counter = Counter(names)
        return [k for k, v in counter.items() if v > 1]

    def _format_names(self, names):
        return ', '.join('"{}"'.format(name) for name in names)

    def _format_types(self, objects):
        return ', '.join(map(repr, set(type(obj) for obj in objects)))

    def _format_path(self, obj=None):
        path = self._ctx + ([obj] if obj is not None else [])
        return ''.join(self._name_formatter.visit(i) for i in path)

    def visit_option(self, obj):
        # TODO: check option default value according to the option type
        pass

    def visit_link(self, obj):
        invalid = [f for f in obj.options
                   if not isinstance(f, self._link_accept_types)]
        if invalid:
            self.errors.report(
                'Invalid types provided as link "{}" options: {}'
                .format(self._format_path(obj), self._format_types(invalid))
            )
            return

        with self.push_ctx(obj):
            super(GraphValidator, self).visit_link(obj)

        graph_nodes_map = {e.name for e in self.items if e.name is not None}
        if obj.node not in graph_nodes_map:
            self.errors.report(
                'Link "{}" points to the missing node "{}"'
                .format(self._format_path(obj), obj.node)
            )

        if obj.requires is not None:
            if obj.requires not in self.ctx.fields_map:
                self.errors.report(
                    'Link "{}" requires missing field "{}" in the "{}" node'
                    .format(obj.name, obj.requires, self._format_path())
                )

    def _generic_visit_node(self, obj, node_name):
        invalid = [f for f in obj.fields
                   if not isinstance(f, self._node_accept_types)]
        if invalid:
            self.errors.report(
                'Node can not contain these types: {} in node "{}"'
                .format(self._format_types(invalid), node_name)
            )
            return

        with self.push_ctx(obj):
            for item in obj.fields:
                self.visit(item)

        duplicates = self._get_duplicates(e.name for e in obj.fields)
        if duplicates:
            self.errors.report(
                'Duplicated names found in the "{}" node: {}'
                .format(node_name, self._format_names(duplicates))
            )

    def visit_node(self, obj):
        self._generic_visit_node(obj, obj.name)
        nodes = [f.name for f in obj.fields if isinstance(f, AbstractNode)]
        if nodes:
            self.errors.report(
                'Node can not be defined in the non-root node: '
                '{} in "{}"'
                .format(self._format_names(nodes), obj.name)
            )

    def visit_root(self, obj):
        self._generic_visit_node(obj, 'root')

    def visit_graph(self, obj):
        self.visit_graph_items(obj.items)

    def visit_graph_items(self, items):
        invalid = [f for f in items
                   if not isinstance(f, self._graph_accept_types)]
        if invalid:
            self.errors.report(
                'Graph can not contain these types: {}'
                .format(self._format_types(invalid))
            )
            return

        root = Root(list(chain.from_iterable(e.fields for e in items
                                             if e.name is None)))
        self.visit(root)

        for item in items:
            if item.name is not None:
                self.visit(item)

        duplicates = self._get_duplicates(e.name for e in items
                                          if e.name is not None)
        if duplicates:
            self.errors.report('Duplicated nodes found in the graph: {}'
                               .format(self._format_names(duplicates)))
