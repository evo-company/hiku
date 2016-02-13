from .. import query
from ..refs import RequirementsExtractor
from ..graph import Link, Field
from ..query import merge
from ..engine import Query, store_fields
from ..checker import check
from ..compiler import ExpressionCompiler


THIS_LINK_NAME = '__link_to_this'


def _create_result_proc(query, env, edge, fields, procs, options, ids):
    def result_proc(result):
        sq_result = query.result()
        store_fields(result, edge, fields, ids, [
            [proc(this, env, sq_result, opts)
             for proc, opts in zip(procs, options)]
            for this in sq_result[THIS_LINK_NAME]
        ])
    return result_proc


def subquery_fields(sub_root, sub_edge_name, exprs):
    re_env = {}
    for expr in exprs:
        re_env.update(expr.functions)
    ec_env = {func.__fn_name__ for func in re_env.values()}
    fn_env = {func.__fn_name__: func.fn for func in re_env.values()}

    re_env['this'] = sub_root.fields[sub_edge_name]
    re_env.update(sub_root.fields)

    reqs_map = {}
    procs_map = {}
    for expr in exprs:
        ce_env = dict(re_env, **expr.options)
        expr_node = check(ce_env, expr.node)
        reqs_map[expr.name] = RequirementsExtractor.extract(re_env, expr_node)
        ec = ExpressionCompiler(ec_env, expr.options)
        procs_map[expr.name] = eval(compile(ec.compile_lambda_expr(expr_node),
                                            '<expr>', 'eval'))

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
