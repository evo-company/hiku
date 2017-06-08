from contextlib import contextmanager
from collections import Counter

from ..types import CallableMeta
from ..compat import ast as py, text_type, PY36

from .nodes import Symbol, Keyword


class Environ(object):

    def __init__(self):
        self.vars = Counter()

    def __getitem__(self, key):
        i = self.vars[key]
        return '{}_{}'.format(key, i) if i > 1 else key

    def __contains__(self, key):
        return key in self.vars

    @contextmanager
    def push(self, names):
        for name in names:
            self.vars[name] += 1
        try:
            yield
        finally:
            for name in names:
                self.vars[name] -= 1


class ExpressionCompiler(object):
    ctx_var = 'ctx'
    env_var = 'env'

    def __init__(self):
        self.env = Environ()

    @classmethod
    def compile_expr(cls, node):
        return cls().visit(node)

    @classmethod
    def compile_lambda_expr(cls, node, args=None):
        args = args or []
        compiler = cls()
        with compiler.env.push(['this'] + args):
            body = compiler.visit(node)
        py_args = [py.arg(cls.env_var), py.arg('this'), py.arg(cls.ctx_var)]
        py_args += [py.arg(name) for name in args]
        expr = py.Lambda(py.arguments(py_args, None, None, []), body)
        py.fix_missing_locations(expr)
        return py.Expression(expr)

    def _var_load(self, name):
        return py.Name(name, py.Load())

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
        if isinstance(node, int):
            return py.Num(node)
        elif isinstance(node, text_type):
            return py.Str(node)
        else:
            raise NotImplementedError(type(node))

    def visit_get_expr(self, node):
        _, obj, name = node.values
        assert isinstance(name, Symbol)
        obj_expr = self.visit(obj)
        return py.Subscript(obj_expr, py.Index(py.Str(name.name)), py.Load())

    def visit_if_expr(self, node):
        args = [self.visit(val) for val in node.values[1:]]
        test_expr, then_expr, else_expr = args
        return py.IfExp(test_expr, then_expr, else_expr)

    def visit_if_some_expr(self, node):
        _, bind, then_, else_ = node.values
        bind_sym, bind_expr = bind.values
        with self.env.push([bind_sym.name]):
            none = py.Name('None', py.Load())
            load_bind_sym = py.Name(self.env[bind_sym.name], py.Load())
            test = py.Compare(load_bind_sym, [py.IsNot()], [none])
            store_bind_sym = py.Name(self.env[bind_sym.name], py.Store())
            comp = py.comprehension(
                store_bind_sym,
                py.Tuple([self.visit(bind_expr)], py.Load()),
                [],
            )
            expr = py.IfExp(test, self.visit(then_), self.visit(else_))
        gen = py.GeneratorExp(expr, [comp])
        return py.Call(py.Name('next', py.Load()), [gen], [], None, None)

    def visit_each_expr(self, node):
        sym, var, col, body = node.values
        assert isinstance(var, Symbol)
        col_expr = self.visit(col)
        with self.env.push([var.name]):
            var_name = self.env[var.name]
            body_expr = self.visit(body)
        py_comp_extra = [0] if PY36 else []  # comprehension:is_async
        return py.ListComp(body_expr,
                           [py.comprehension(py.Name(var_name, py.Store()),
                                             col_expr, [], *py_comp_extra)])

    def visit_tuple(self, node):
        sym = node.values[0]
        if sym.name == 'get':
            return self.visit_get_expr(node)
        elif sym.name == 'if':
            return self.visit_if_expr(node)
        elif sym.name == 'if_some':
            return self.visit_if_some_expr(node)
        elif sym.name == 'each':
            return self.visit_each_expr(node)
        else:
            values = [self.visit(node) for node in node.values]
            sym_expr, arg_exprs = values[0], values[1:]
            return py.Call(sym_expr, arg_exprs, [], None, None)

    def visit_symbol(self, node):
        if node.name in self.env:
            return self._var_load(self.env[node.name])
        elif isinstance(node.__ref__.to, CallableMeta):
            return self._env_load(node.name)
        else:
            return self._ctx_load(node.name)

    def visit_list(self, node):
        return py.List([self.visit(value) for value in node.values],
                       py.Load())

    def visit_dict(self, node):
        assert not len(node.values) % 2, 'Probably missing keyword value'
        keys = node.values[::2]
        values = node.values[1::2]
        assert all(isinstance(k, Keyword) for k in keys), 'Wrong arguments'
        return py.Dict([py.Str(key.name) for key in keys],
                       [self.visit(value) for value in values])
