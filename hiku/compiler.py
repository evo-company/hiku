from .nodes import Symbol
from .compat import ast as py


class ExpressionCompiler(object):
    ctx_var = 'ctx'
    env_var = 'env'

    def __init__(self, env):
        self.env = set(env)
        self.vars = set([])

    def _ctx_load(self, name):
        return py.Subscript(py.Name(self.ctx_var, py.Load()),
                            py.Index(py.Str(name)), py.Load())

    def _env_load(self, name):
        return py.Subscript(py.Name(self.env_var, py.Load()),
                            py.Index(py.Str(name)), py.Load())

    def visit(self, node):
        if hasattr(node, 'accept'):
            return node.accept(self)
        else:
            return self.generic_visit(node)

    def generic_visit(self, node):
        return node

    def visit_get_expr(self, node):
        _, obj, name = node.values
        assert isinstance(name, Symbol)
        obj_expr = self.visit(obj)
        return py.Subscript(obj_expr, py.Index(py.Str(name.name)), py.Load())

    def visit_if_expr(self, node):
        args = [self.visit(val) for val in node.values[1:]]
        test_expr, then_expr, else_expr = args
        return py.IfExp(test_expr, then_expr, else_expr)

    def visit_each_expr(self, node):
        sym, var, col, body = node.values
        assert isinstance(var, Symbol)
        col_expr = self.visit(col)
        # TODO: implement proper scoping
        self.vars.add(var.name)
        body_expr = self.visit(body)
        self.vars.discard(var.name)
        return py.ListComp(body_expr,
                           [py.comprehension(py.Name(var.name, py.Store()),
                                             col_expr, [])])

    def visit_tuple(self, node):
        sym = node.values[0]
        if sym.name == 'get':
            return self.visit_get_expr(node)
        elif sym.name == 'if':
            return self.visit_if_expr(node)
        elif sym.name == 'each':
            return self.visit_each_expr(node)
        elif sym.name in self.env:
            values = [self.visit(node) for node in node.values]
            sym_expr, arg_exprs = values[0], values[1:]
            return py.Call(sym_expr, arg_exprs, [], None, None)
        else:
            raise ValueError('Unknown function name: {!r}'.format(sym.name))

    def visit_symbol(self, node):
        if node.name in self.vars:
            return py.Name(node.name, py.Load())
        elif node.name in self.env:
            return self._env_load(node.name)
        else:
            return self._ctx_load(node.name)
