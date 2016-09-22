from ..types import TypingMeta
from ..compat import with_metaclass


class TypeDefMeta(TypingMeta):

    def __cls_init__(cls, params):
        cls.__type_name__, cls.__type__ = params

    def accept(cls, visitor):
        return visitor.visit_typedef(cls)


class TypeDef(with_metaclass(TypeDefMeta, object)):
    pass
