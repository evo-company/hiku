from itertools import chain

from .. import query
from ..graph import Link, Field, Nothing
from ..types import TypeRef, Sequence
from ..query import merge
from ..types import Unknown
from ..engine import Query, store_fields, subquery
from ..expr.refs import RequirementsExtractor
from ..expr.core import to_expr
from ..expr.checker import check, graph_types, fn_types
from ..expr.compiler import ExpressionCompiler


THIS_LINK_NAME = '__link_to_this'


def _create_result_proc(query, env, node, fields, procs, options, ids):
    def result_proc(result):
        sq_result = query.result()
        store_fields(result, node, fields, ids, [
            [proc(this, env, sq_result, *opt_args)
             for proc, opt_args in zip(procs, options)]
            for this in sq_result[THIS_LINK_NAME]
        ])
    return result_proc


class Expr(Field):

    def __init__(self, name, subquery, *other, **kwargs):
        if not len(other):
            raise TypeError('Missing required argument')
        elif len(other) == 1:
            type_, expr = None, other[0]
        elif len(other) == 2:
            type_, expr = other
        else:
            raise TypeError('More positional arguments ({}) than expected (2)'
                            .format(len(other)))

        super(Expr, self).__init__(name, type_, subquery, **kwargs)
        self.expr = expr

        expr_node, functions = to_expr(expr)

        self.functions = functions

        types = subquery.types.copy()
        types.update(fn_types(self.functions))
        types.update({opt.name: Unknown for opt in self.options})

        expr_node = check(expr_node, types)

        options_set = set(self.options_map)
        query_node = RequirementsExtractor.extract(types, expr_node)
        query_node = query.Node([f for f in query_node.fields
                                 if f.name not in options_set])
        self.reqs = query_node

        option_names = [opt.name for opt in self.options]
        code = ExpressionCompiler.compile_lambda_expr(expr_node, option_names)
        self.proc = eval(compile(code, '<expr>', 'eval'))

    def accept(self, visitor):
        return visitor.visit_expr(self)


def _yield_options(query_field, graph_field):
    options = query_field.options or {}
    for option in graph_field.options:
        value = options.get(option.name, option.default)
        if value is Nothing:
            raise TypeError('Required option "{}" for {!r} was not provided'
                            .format(option.name, graph_field))
        else:
            yield value


@subquery
class SubGraph(object):

    def __init__(self, graph, node):
        self.graph = graph
        self.node = node

        types = graph_types(graph)
        types['this'] = types[node]  # make an alias
        self.types = types

    def __call__(self, queue, ctx, task_set, node, fields, ids):
        graph_fields = [node.fields_map[f.name] for f in fields]
        fn_env = {f.__def_name__: f.__def_body__
                  for f in chain.from_iterable(e.functions
                                               for e in graph_fields)}

        this_link = Link(THIS_LINK_NAME, Sequence[TypeRef[self.node]],
                         None, requires=None)

        reqs = merge(f.reqs for f in graph_fields)
        procs = [f.proc for f in graph_fields]
        options = [list(_yield_options(qf, gf))
                   for qf, gf in zip(fields, graph_fields)]

        this_req = reqs.fields_map['this'].node
        other_reqs = query.Node([r for r in reqs.fields
                                 if r.name != 'this'])

        q = Query(queue, task_set, self.graph, ctx)
        q.process_link(self.graph.root, this_link, this_req, None, ids)
        q.process_node(self.graph.root, other_reqs, None)
        return _create_result_proc(q, fn_env, node, fields, procs,
                                   options, ids)
