from collections import OrderedDict


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


class Record(object):

    def __init__(self, fields):
        self.fields = OrderedDict(fields)

    def accept(self, visitor):
        return visitor.visit_record(self)
