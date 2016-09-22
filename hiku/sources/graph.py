from itertools import chain

from .. import query
from ..refs import RequirementsExtractor
from ..expr import to_expr
from ..graph import Link, Field
from ..types import TypeRef, Sequence
from ..query import merge
from ..utils import kw_only
from ..types import Unknown
from ..engine import Query, store_fields, subquery
from ..checker import check, graph_types, fn_types
from ..compiler import ExpressionCompiler


THIS_LINK_NAME = '__link_to_this'


def _create_result_proc(query, env, edge, fields, procs, options, ids):
    def result_proc(result):
        sq_result = query.result()
        store_fields(result, edge, fields, ids, [
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

        options, description = kw_only(kwargs, [], ['options', 'description'])

        super(Expr, self).__init__(name, type_, subquery,
                                   options=options, description=description)

        node, functions = to_expr(expr)

        self.functions = functions

        types = subquery.types.copy()
        types.update(fn_types(self.functions))
        types.update({opt.name: Unknown for opt in self.options})

        node = check(node, types)

        options_set = set(self.options_map)
        edge = RequirementsExtractor.extract(types, node)
        edge = query.Edge([f for f in edge.fields
                           if f.name not in options_set])
        self.reqs = edge

        option_names = [opt.name for opt in self.options]
        self.option_defaults = [(opt.name, opt.default) for opt in self.options]
        code = ExpressionCompiler.compile_lambda_expr(node, option_names)
        self.proc = eval(compile(code, '<expr>', 'eval'))


@subquery
class SubGraph(object):

    def __init__(self, graph, edge):
        self.graph = graph
        self.edge = edge

        types = graph_types(graph)
        types['this'] = types[edge]  # make an alias
        self.types = types

    def __call__(self, queue, ctx, task_set, edge, fields, ids):
        graph_fields = [edge.fields_map[f.name] for f in fields]
        fn_env = {f.__def_name__: f.__def_body__
                  for f in chain.from_iterable(e.functions
                                               for e in graph_fields)}

        this_link = Link(THIS_LINK_NAME, Sequence[TypeRef[self.edge]],
                         None, requires=None)

        reqs = merge(f.reqs for f in graph_fields)
        procs = [f.proc for f in graph_fields]
        options = [[qf.options.get(name, default) if qf.options else default
                    for name, default in gf.option_defaults]
                   for qf, gf in zip(fields, graph_fields)]

        this_req = reqs.fields_map['this'].edge
        other_reqs = query.Edge([r for r in reqs.fields
                                 if r.name != 'this'])

        q = Query(queue, task_set, self.graph, ctx)
        q.process_link(self.graph.root, this_link, this_req, None, ids)
        q.process_edge(self.graph.root, other_reqs, None)
        return _create_result_proc(q, fn_env, edge, fields, procs,
                                   options, ids)
