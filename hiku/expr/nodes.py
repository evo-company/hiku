class Node(object):

    def accept(self, visitor):
        raise NotImplementedError


class Symbol(Node):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def accept(self, visitor):
        return visitor.visit_symbol(self)


class Keyword(Node):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return ':{}'.format(self.name)

    def accept(self, visitor):
        return visitor.visit_keyword(self)


class Tuple(Node):

    def __init__(self, values):
        self.values = tuple(values)

    def __repr__(self):
        return '({})'.format(' '.join(map(repr, self.values)))

    def accept(self, visitor):
        return visitor.visit_tuple(self)


class List(Node):

    def __init__(self, values):
        self.values = tuple(values)

    def __repr__(self):
        return '[{}]'.format(' '.join(map(repr, self.values)))

    def accept(self, visitor):
        return visitor.visit_list(self)


class Dict(Node):

    def __init__(self, values):
        self.values = tuple(values)

    def __repr__(self):
        return '{{{}}}'.format(' '.join(map(repr, self.values)))

    def accept(self, visitor):
        return visitor.visit_dict(self)


class NodeVisitor(object):

    def visit(self, node):
        if hasattr(node, 'accept'):
            node.accept(self)
        else:
            self.generic_visit(node)

    def generic_visit(self, node):
        pass

    def visit_symbol(self, node):
        pass

    def visit_keyword(self, node):
        pass

    def visit_tuple(self, node):
        for value in node.values:
            self.visit(value)

    def visit_list(self, node):
        for value in node.values:
            self.visit(value)

    def visit_dict(self, node):
        for value in node.values:
            self.visit(value)


class NodeTransformer(object):

    def visit(self, node):
        if hasattr(node, 'accept'):
            return node.accept(self)
        else:
            return self.generic_visit(node)

    def generic_visit(self, node):
        return node

    def visit_symbol(self, node):
        return Symbol(node.name)

    def visit_keyword(self, node):
        return Keyword(node.name)

    def visit_tuple(self, node):
        return Tuple(self.visit(value)
                     for value in node.values)

    def visit_list(self, node):
        return List(self.visit(value)
                    for value in node.values)

    def visit_dict(self, node):
        return Dict(self.visit(value)
                    for value in node.values)
