from ..types import TypingMeta, GenericMeta
from ..compat import with_metaclass


class TypeDefMeta(TypingMeta):

    def __cls_init__(cls, params):
        cls.__type_name__, cls.__type__ = params

    def accept(cls, visitor):
        return visitor.visit_typedef(cls)


class TypeDef(with_metaclass(TypeDefMeta, object)):
    pass


class TypeRefMeta(TypingMeta):

    def __cls_init__(cls, name):
        cls.__type_name__ = name

    def accept(cls, visitor):
        return visitor.visit_typeref(cls)


class TypeRef(with_metaclass(TypeRefMeta, object)):
    pass


class UnknownMeta(GenericMeta):

    def accept(cls, visitor):
        return visitor.visit_unknown(cls)


class Unknown(with_metaclass(UnknownMeta, object)):
    pass
