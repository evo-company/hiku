class Type(object):

    def accept(self, visitor):
        raise NotImplementedError


class StringType(Type):

    def accept(self, visitor):
        return visitor.visit_string(self)


class IntegerType(Type):

    def accept(self, visitor):
        return visitor.visit_integer(self)


class ListType(Type):

    def __init__(self, item_type):
        self.item_type = item_type

    def accept(self, visitor):
        return visitor.visit_list(self)
