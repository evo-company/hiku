from collections import OrderedDict

from .compat import with_metaclass


class GenericMeta(type):

    def __repr__(cls):
        return cls.__name__

    def accept(cls, visitor):
        raise NotImplementedError


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
