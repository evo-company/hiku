from collections import OrderedDict


class Type(object):

    def accept(self, visitor):
        raise NotImplementedError


class BooleanType(Type):

    def accept(self, visitor):
        return visitor.visit_boolean(self)


class StringType(Type):

    def accept(self, visitor):
        return visitor.visit_string(self)


class IntegerType(Type):

    def accept(self, visitor):
        return visitor.visit_integer(self)


class ContainerType(Type):
    pass


class OptionType(ContainerType):

    def __init__(self, type_):
        self.type = type_

    def accept(self, visitor):
        return visitor.visit_option(self)


class ListType(ContainerType):

    def __init__(self, item_type):
        self.item_type = item_type

    def accept(self, visitor):
        return visitor.visit_list(self)


class DictType(ContainerType):

    def __init__(self, key_type, value_type):
        self.key_type = key_type
        self.value_type = value_type

    def accept(self, visitor):
        return visitor.visit_dict(self)


class RecordType(ContainerType):

    def __init__(self, fields):
        self.fields = OrderedDict(fields)

    def accept(self, visitor):
        return visitor.visit_record(self)
