class Node(object):

    def accept(self, visitor):
        raise NotImplementedError


class Symbol(Node):

    def __init__(self, name):
        self.name = name

    def accept(self, visitor):
        return visitor.visit_symbol(self)

    def __repr__(self):
        return self.name


class Tuple(Node):

    def __init__(self, values):
        self.values = tuple(values)

    def __repr__(self):
        return '({})'.format(' '.join(map(repr, self.values)))

    def accept(self, visitor):
        return visitor.visit_tuple(self)
