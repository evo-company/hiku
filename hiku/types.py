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


def to_instance(type_):
    if isinstance(type_, type):
        if issubclass(type_, ContainerType):
            raise TypeError('Type {!r} is not instantiated'.format(type_))
        else:
            return type_()
    else:
        return type_


class OptionType(ContainerType):

    def __init__(self, type_):
        self.type = to_instance(type_)

    def accept(self, visitor):
        return visitor.visit_option(self)


class ListType(ContainerType):

    def __init__(self, item_type):
        self.item_type = to_instance(item_type)

    def accept(self, visitor):
        return visitor.visit_list(self)


class DictType(ContainerType):

    def __init__(self, key_type, value_type):
        self.key_type = to_instance(key_type)
        self.value_type = to_instance(value_type)

    def accept(self, visitor):
        return visitor.visit_dict(self)


class RecordType(ContainerType):

    def __init__(self, fields):
        self.fields = OrderedDict(
            (k, to_instance(v)) for k, v in OrderedDict(fields).items()
        )

    def accept(self, visitor):
        return visitor.visit_record(self)


class FunctionType(Type):

    def __init__(self, arg_types):
        self.arg_types = arg_types

    def accept(self, visitor):
        return visitor.visit_function(self)
