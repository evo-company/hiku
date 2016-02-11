class TypeDef(object):

    def __init__(self, name, fields):
        self.name = name
        self.type = fields

    def accept(self, visitor):
        return visitor.visit_typedef(self)


class TypeRef(object):

    def __init__(self, name):
        self.name = name

    def accept(self, visitor):
        return visitor.visit_typeref(self)


class UnknownType(object):

    def accept(self, visitor):
        return visitor.visit_unknown(self)
