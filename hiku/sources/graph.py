from .. import query
from ..refs import RequirementsExtractor
from ..graph import Link, Field
from ..query import merge
from ..engine import Query, store_fields
from ..checker import check, graph_types, fn_types
from ..compiler import ExpressionCompiler
from ..typedef.types import UnknownType


THIS_LINK_NAME = '__link_to_this'


def _create_result_proc(query, env, edge, fields, procs, options, ids):
    def result_proc(result):
        sq_result = query.result()
        store_fields(result, edge, fields, ids, [
            [proc(this, env, sq_result)  # FIXME: fix options support
             for proc, opts in zip(procs, options)]
            for this in sq_result[THIS_LINK_NAME]
        ])
    return result_proc


def subquery_fields(sub_root, sub_edge_name, exprs):
    types = graph_types(sub_root)

    # make an alias
    types['this'] = types[sub_edge_name]

    reqs_map = {}
    procs_map = {}
    funcs_set = set([])
    for expr in exprs:
        expr_types = types.copy()
        expr_types.update(fn_types(expr.functions))
        expr_types.update({opt.name: UnknownType()
                           for opt in expr.options.values()})
        expr_node = check(expr.node, expr_types)

        reqs_map[expr.name] = \
            RequirementsExtractor.extract(expr_types, expr_node)

        code = ExpressionCompiler.compile_lambda_expr(expr_node)
        procs_map[expr.name] = eval(compile(code, '<expr>', 'eval'))

        funcs_set.update(expr.functions)

    fn_env = {f.__fn_name__: f.fn for f in funcs_set}

    def query_func(queue, task_set, edge, fields, ids):
        this_link = Link(THIS_LINK_NAME, None, sub_edge_name, None,
                         to_list=True)

        reqs = merge(reqs_map[f.name] for f in fields)
        procs = [procs_map[f.name] for f in fields]
        options = [f.options for f in fields]

        this_req = reqs.fields['this'].edge
        other_reqs = query.Edge([r for r in reqs.fields.values()
                                 if r.name != 'this'])

        q = Query(queue, task_set, sub_root)
        q.process_link(sub_root, this_link, this_req, None, ids)
        q.process_edge(sub_root, other_reqs, None)
        return _create_result_proc(q, fn_env, edge, fields, procs, options, ids)

    query_func.__subquery__ = True

    return [Field(expr.name, expr.type, query_func,
                  options=expr.options.values(), doc=expr.doc)
            for expr in exprs]
