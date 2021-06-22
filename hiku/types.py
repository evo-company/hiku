from abc import abstractmethod, ABC
from collections import OrderedDict


class GenericMeta(type):

    def __repr__(cls):
        return cls.__name__

    def __eq__(cls, other):
        return (cls.__class__ is other.__class__
                and cls.__dict__ == other.__dict__)

    def __ne__(cls, other):
        return not cls.__eq__(other)

    def accept(cls, visitor):
        raise NotImplementedError(type(cls))


class AnyMeta(GenericMeta):

    def accept(cls, visitor):
        return visitor.visit_any(cls)


class Any(metaclass=AnyMeta):
    pass


class BooleanMeta(GenericMeta):

    def accept(cls, visitor):
        return visitor.visit_boolean(cls)


class Boolean(metaclass=BooleanMeta):
    pass


class StringMeta(GenericMeta):

    def accept(cls, visitor):
        return visitor.visit_string(cls)


class String(metaclass=StringMeta):
    pass


class IntegerMeta(GenericMeta):

    def accept(cls, visitor):
        return visitor.visit_integer(cls)


class Integer(metaclass=IntegerMeta):
    pass


class FloatMeta(GenericMeta):

    def accept(cls, visitor):
        return visitor.visit_float(cls)


class Float(metaclass=FloatMeta):
    pass


class TypingMeta(GenericMeta):
    __final__ = False

    def __cls_init__(cls, *args):
        raise NotImplementedError(type(cls))

    def __cls_repr__(cls):
        raise NotImplementedError(type(cls))

    def __getitem__(cls, parameters):
        if cls.__final__:
            raise TypeError('Cannot substitute parameters in {!r}'.format(cls))
        type_ = cls.__class__(cls.__name__, cls.__bases__, dict(cls.__dict__))
        type_.__cls_init__(parameters)
        type_.__final__ = True
        return type_

    def __repr__(self):
        if self.__final__:
            return self.__cls_repr__()
        else:
            return super(TypingMeta, self).__repr__()


class OptionalMeta(TypingMeta):

    def __cls_init__(cls, type_):
        cls.__type__ = _maybe_typeref(type_)

    def __cls_repr__(self):
        return '{}[{!r}]'.format(self.__name__, self.__type__)

    def accept(cls, visitor):
        return visitor.visit_optional(cls)


class Optional(metaclass=OptionalMeta):
    pass


class SequenceMeta(TypingMeta):

    def __cls_init__(cls, item_type):
        cls.__item_type__ = _maybe_typeref(item_type)

    def __cls_repr__(self):
        return '{}[{!r}]'.format(self.__name__, self.__item_type__)

    def accept(cls, visitor):
        return visitor.visit_sequence(cls)


class Sequence(metaclass=SequenceMeta):
    pass


class MappingMeta(TypingMeta):

    def __cls_init__(cls, params):
        key_type, value_type = params
        cls.__key_type__ = _maybe_typeref(key_type)
        cls.__value_type__ = _maybe_typeref(value_type)

    def __cls_repr__(self):
        return '{}[{!r}, {!r}]'.format(self.__name__, self.__key_type__,
                                       self.__value_type__)

    def accept(cls, visitor):
        return visitor.visit_mapping(cls)


class Mapping(metaclass=MappingMeta):
    pass


class RecordMeta(TypingMeta):

    def __cls_init__(cls, field_types):
        if hasattr(field_types, 'items'):
            items = field_types.items()
        else:
            items = field_types
        cls.__field_types__ = OrderedDict(
            (key, _maybe_typeref(val)) for key, val in items
        )

    def __cls_repr__(self):
        return '{}[{!r}]'.format(self.__name__, dict(self.__field_types__))

    def accept(cls, visitor):
        return visitor.visit_record(cls)


class Record(metaclass=RecordMeta):
    pass


class CallableMeta(TypingMeta):

    def __cls_init__(cls, arg_types):
        cls.__arg_types__ = [_maybe_typeref(t) for t in arg_types]

    def __cls_repr__(self):
        return '{}[{}]'.format(self.__name__,
                               ', '.join(map(repr, self.__arg_types__)))

    def accept(cls, visitor):
        return visitor.visit_callable(cls)


class Callable(metaclass=CallableMeta):
    pass


class TypeRefMeta(TypingMeta):

    def __cls_init__(cls, name):
        cls.__type_name__ = name

    def __cls_repr__(self):
        return '{}[{!r}]'.format(self.__name__, self.__type_name__)

    def accept(cls, visitor):
        return visitor.visit_typeref(cls)


class TypeRef(metaclass=TypeRefMeta):
    pass


def _maybe_typeref(t):
    return TypeRef[t] if isinstance(t, str) else t


class AbstractTypeVisitor(ABC):

    def visit(self, obj):
        return obj.accept(self)

    @abstractmethod
    def visit_any(self, obj):
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
    def visit_float(self, obj):
        pass

    @abstractmethod
    def visit_typeref(self, obj):
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

    def visit_any(self, obj):
        pass

    def visit_boolean(self, obj):
        pass

    def visit_string(self, obj):
        pass

    def visit_integer(self, obj):
        pass

    def visit_float(self, obj):
        pass

    def visit_typeref(self, obj):
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


def get_type(types, t):
    if isinstance(t, TypeRefMeta):
        return types[t.__type_name__]
    else:
        return t
