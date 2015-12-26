from .compat import ast as py


class ExpressionCompiler(object):

    def visit(self, node):
        if hasattr(node, 'accept'):
            return node.accept(self)
        else:
            return self.generic_visit(node)

    def generic_visit(self, node):
        return node

    def visit_tuple(self, node):
        sym, args = node.values[0], node.values[1:]
        name_expr = py.Attribute(py.Name('env', py.Load()),
                                 sym.name, py.Load())
        return py.Call(name_expr,
                       [self.visit(arg) for arg in args],
                       [], None, None)

    def visit_symbol(self, node):
        return py.Name(node.name, py.Load())
