from hiku.graph import Link, Field
from hiku.query import merge, RequirementsExtractor
from hiku.engine import Query, store_fields
from hiku.compiler import ExpressionCompiler


THIS_LINK_NAME = '__link_to_this'


def _create_result_proc(query, env, edge, fields, field_procs, ids):
    def result_proc(store):
        store_fields(store, edge, fields, ids, [
            [field_proc(this, env, query.store) for field_proc in field_procs]
            for this in query.store[THIS_LINK_NAME]
        ])
    return result_proc


def subquery_fields(sub_root, sub_edge_name, funcs, exprs):
    ec_env = {func.__fn_name__ for func in funcs}
    re_env = {func.__fn_name__: func for func in funcs}
    fn_env = {func.__fn_name__: func.fn for func in funcs}

    ec = ExpressionCompiler(ec_env)
    reqs_map = {}
    procs_map = {}
    for name, expr in exprs.items():
        re = RequirementsExtractor(re_env)
        re.visit(expr)
        reqs_map[name] = re.get_requirements()
        procs_map[name] = eval(compile(ec.compile_lambda_expr(expr),
                                       '<expr>', 'eval'))

    def query_func(queue, task_set, edge, fields, ids):
        this_link = Link(THIS_LINK_NAME, None, sub_edge_name, None, True)

        reqs = merge(reqs_map[f.name] for f in fields)
        procs = [procs_map[f.name] for f in fields]

        query = Query(queue, task_set, sub_root, None)
        query._process_link(sub_root, this_link, reqs, None, ids)

        return _create_result_proc(query, fn_env, edge, fields, procs, ids)

    query_func.__subquery__ = True

    return [Field(name, query_func) for name in exprs.keys()]
