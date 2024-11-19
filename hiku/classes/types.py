import dataclasses as dc
import importlib
import inspect
import types
import typing
from collections.abc import Hashable

import hiku.graph
import hiku.types

_T = typing.TypeVar("_T", bound=Hashable)


class NodeProto(typing.Protocol[_T]):
    __key__: _T


_TNode = typing.TypeVar("_TNode", bound=NodeProto)


@dc.dataclass
class raw_type:
    """
    Helps to update hiku types gradually. E.g.

    id: typing.Annotated[str, hiku.raw_type(hiku.types.ID)]
    some_field: typing.Annotated[None, hiku.raw_type(TypeRef["Product"])]
    """

    typ: hiku.types.GenericMeta

    def apply(
        self,
        container: hiku.types.OptionalMeta | hiku.types.SequenceMeta,
    ) -> typing.Self:
        return dc.replace(self, typ=container[self.typ])

    def __hash__(self) -> int:
        return hash(self.typ)


class lazy:
    """
    Allows for a lazy type resolve when circular imports are encountered.
    Lazy resolvers are processed during Graph.__init__
    """

    module: str
    package: str | None

    def __init__(self, module: str):
        self.module = module
        self.package = None

        if module.startswith("."):
            current_frame = inspect.currentframe()
            assert current_frame is not None
            assert current_frame.f_back is not None

            self.package = current_frame.f_back.f_globals["__package__"]


class ref(typing.Generic[_TNode]):
    """Represents a reference to another object type.

    Is needed in case we someday plan to implement proper mypy checks - this way
    we can make use of ref object as a thin wrapper around type's __key__
    """


_BUILTINS_TO_HIKU = {
    int: hiku.types.Integer,
    float: hiku.types.Float,
    str: hiku.types.String,
    bool: hiku.types.Boolean,
}


@dc.dataclass
class _LazyTypeRef:
    """strawberry-like impl for lazy type refs"""

    classname: str
    module: str
    package: str | None
    containers: (
        list[hiku.types.OptionalMeta | hiku.types.SequenceMeta] | None
    ) = None

    @property
    def typ(self) -> hiku.types.GenericMeta:
        module = importlib.import_module(self.module, self.package)
        cls = module.__dict__[self.classname]

        type_ref = hiku.types.TypeRef[cls.__hiku_node__.name]

        containers = reversed(self.containers or [])
        for c in containers:
            type_ref = c[type_ref]

        return type_ref

    def apply(
        self,
        container: hiku.types.OptionalMeta | hiku.types.SequenceMeta,
    ) -> typing.Self:
        return dc.replace(
            self,
            containers=[container] + (self.containers or []),
        )


class _HikuTypeWrapperProto(typing.Protocol):

    @property
    def typ(self) -> hiku.types.GenericMeta: ...

    def apply(
        self, container: hiku.types.OptionalMeta | hiku.types.SequenceMeta
    ) -> typing.Self: ...


def to_hiku_type(typ: type, lazy_: lazy | None = None) -> _HikuTypeWrapperProto:
    if typ in _BUILTINS_TO_HIKU:
        return raw_type(_BUILTINS_TO_HIKU[typ])

    origin = typing.get_origin(typ)
    args = typing.get_args(typ)

    if origin is typing.Annotated:
        metadata = typ.__metadata__

        raw_types = []
        lazy_refs = []
        for val in metadata:
            if isinstance(val, raw_type):
                raw_types.append(val)
            elif isinstance(val, lazy):
                lazy_refs.append(val)

        if lazy_refs and raw_types:
            raise ValueError("lazy and raw_type are not composable")

        if len(raw_types) > 1:
            raise ValueError("more than 1 raw_type")

        if len(raw_types) == 1:
            return raw_types[0]

        if len(lazy_refs) > 1:
            raise ValueError("more than 1 lazy reference")

        if len(lazy_refs) == 1:
            lazy_typeref = to_hiku_type(typ.__origin__, lazy_refs[0])
            if not isinstance(lazy_typeref, _LazyTypeRef):
                raise ValueError("lazy can only be used with ref types")

            return lazy_typeref

        return to_hiku_type(args[0])

    # new optionals
    if origin in (typing.Union, types.UnionType):
        if len(args) != 2 or types.NoneType not in args:
            raise ValueError("unions are allowed only as optional types")

        next_type = [a for a in args if a is not types.NoneType][0]
        arg = to_hiku_type(next_type, lazy_)
        return arg.apply(hiku.types.Optional)

    # old optionals
    if origin is typing.Optional:
        arg = to_hiku_type(args[0], lazy_)
        return arg.apply(hiku.types.Optional)

    # lists
    if origin in (list, typing.List):
        if len(args) == 0:
            raise ValueError("naked lists not allowed")

        next_type = args[0]
        arg = to_hiku_type(next_type, lazy_)
        return arg.apply(hiku.types.Sequence)

    if origin is ref:
        ref_ = args[0]
        if isinstance(ref_, typing.ForwardRef):
            if lazy_ is None:
                raise ValueError("need to use hiku.lazy for lazy imports")

            return _LazyTypeRef(
                classname=ref_.__forward_arg__,
                module=lazy_.module,
                package=lazy_.package,
            )

        if not hasattr(ref_, "__hiku_node__"):
            raise ValueError("expected ref arg to be a @node")

        return raw_type(hiku.types.TypeRef[ref_.__hiku_node__.name])

    raise ValueError("invalid hiku type")
