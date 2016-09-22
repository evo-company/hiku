from abc import abstractmethod, ABCMeta
from collections import OrderedDict

from .compat import with_metaclass


class GenericMeta(type):

    def __repr__(cls):
        return cls.__name__

    def accept(cls, visitor):
        raise NotImplementedError


class UnknownMeta(GenericMeta):

    def accept(cls, visitor):
        return visitor.visit_unknown(cls)


class Unknown(with_metaclass(UnknownMeta, object)):
    pass


class BooleanMeta(GenericMeta):

    def accept(cls, visitor):
        return visitor.visit_boolean(cls)


class Boolean(with_metaclass(BooleanMeta, object)):
    pass


class StringMeta(GenericMeta):

    def accept(cls, visitor):
        return visitor.visit_string(cls)


class String(with_metaclass(StringMeta, object)):
    pass


class IntegerMeta(GenericMeta):

    def accept(cls, visitor):
        return visitor.visit_integer(cls)


class Integer(with_metaclass(IntegerMeta, object)):
    pass


class TypingMeta(GenericMeta):

    def __cls_init__(cls, *args):
        raise NotImplementedError

    def __getitem__(cls, parameters):
        type_ = cls.__class__(cls.__name__, cls.__bases__, dict(cls.__dict__))
        type_.__cls_init__(parameters)
        return type_


class OptionalMeta(TypingMeta):

    def __cls_init__(cls, type_):
        cls.__type__ = type_

    def accept(cls, visitor):
        return visitor.visit_optional(cls)


class Optional(with_metaclass(OptionalMeta, object)):
    pass


class SequenceMeta(TypingMeta):

    def __cls_init__(cls, item_type):
        cls.__item_type__ = item_type

    def accept(cls, visitor):
        return visitor.visit_sequence(cls)


class Sequence(with_metaclass(SequenceMeta, object)):
    pass


class MappingMeta(TypingMeta):

    def __cls_init__(cls, params):
        cls.__key_type__, cls.__value_type__ = params

    def accept(cls, visitor):
        return visitor.visit_mapping(cls)


class Mapping(with_metaclass(MappingMeta, object)):
    pass


class RecordMeta(TypingMeta):

    def __cls_init__(cls, field_types):
        cls.__field_types__ = OrderedDict(field_types)

    def accept(cls, visitor):
        return visitor.visit_record(cls)


class Record(with_metaclass(RecordMeta, object)):
    pass


class CallableMeta(TypingMeta):

    def __cls_init__(cls, arg_types):
        cls.__arg_types__ = arg_types

    def accept(cls, visitor):
        return visitor.visit_callable(cls)


class Callable(with_metaclass(CallableMeta, object)):
    pass


class TypeRefMeta(TypingMeta):

    def __cls_init__(cls, name):
        cls.__type_name__ = name

    def accept(cls, visitor):
        return visitor.visit_typeref(cls)


class TypeRef(with_metaclass(TypeRefMeta, object)):
    pass


class AbstractTypeVisitor(with_metaclass(ABCMeta, object)):

    @abstractmethod
    def visit(self, obj):
        pass

    @abstractmethod
    def visit_boolean(self, obj):
        pass

    @abstractmethod
    def visit_string(self, obj):
        pass

    @abstractmethod
    def visit_integer(self, obj):
        pass

    @abstractmethod
    def visit_optional(self, obj):
        pass

    @abstractmethod
    def visit_sequence(self, obj):
        pass

    @abstractmethod
    def visit_mapping(self, obj):
        pass

    @abstractmethod
    def visit_record(self, obj):
        pass

    @abstractmethod
    def visit_callable(self, obj):
        pass


class TypeVisitor(AbstractTypeVisitor):

    def visit(self, obj):
        return obj.accept(self)

    def visit_boolean(self, obj):
        pass

    def visit_string(self, obj):
        pass

    def visit_integer(self, obj):
        pass

    def visit_optional(self, obj):
        self.visit(obj.__type__)

    def visit_sequence(self, obj):
        self.visit(obj.__item_type__)

    def visit_mapping(self, obj):
        self.visit(obj.__key_type__)
        self.visit(obj.__value_type__)

    def visit_record(self, obj):
        for value_type in obj.__field_types__.values():
            self.visit(value_type)

    def visit_callable(self, obj):
        for arg_type in obj.__arg_types__:
            self.visit(arg_type)
