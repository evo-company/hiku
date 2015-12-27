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
