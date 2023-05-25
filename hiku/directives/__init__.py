import dataclasses
import sys
import typing as t

from collections import OrderedDict
from dataclasses import dataclass
from typing import TYPE_CHECKING
from enum import Enum
from typing_extensions import dataclass_transform

from hiku.utils.typing import builtin_to_introspection_type

if TYPE_CHECKING:
    from hiku.graph import Field, Link


T = t.TypeVar("T", bound=t.Type)


def wrap_dataclass(cls: t.Type[t.Any]) -> t.Type[t.Any]:
    dclass_kwargs: t.Dict[str, bool] = {}
    dclass = dataclasses.dataclass(cls, **dclass_kwargs)

    return dclass


BT = t.TypeVar("BT")


def get_fields(cls: t.Type, by_type: t.Type[BT]) -> t.List[BT]:
    fields: t.List[BT] = []
    for field in dataclasses.fields(cls):
        if isinstance(field, by_type):
            fields.append(field)

    return fields


class Location(Enum):
    # https://spec.graphql.org/June2018/#TypeSystemDirectiveLocation
    SCHEMA = "SCHEMA"
    SCALAR = "SCALAR"
    OBJECT = "OBJECT"
    FIELD_DEFINITION = "FIELD_DEFINITION"
    ARGUMENT_DEFINITION = "ARGUMENT_DEFINITION"
    INTERFACE = "INTERFACE"
    UNION = "UNION"
    ENUM = "ENUM"
    ENUM_VALUE = "ENUM_VALUE"
    INPUT_OBJECT = "INPUT_OBJECT"
    INPUT_FIELD_DEFINITION = "INPUT_FIELD_DEFINITION"
    # https://spec.graphql.org/June2018/#ExecutableDirectiveLocation
    QUERY = "QUERY"
    MUTATION = "MUTATION"
    SUBSCRIPTION = "SUBSCRIPTION"
    FIELD = "FIELD"
    FRAGMENT_DEFINITION = "FRAGMENT_DEFINITION"
    FRAGMENT_SPREAD = "FRAGMENT_SPREAD"
    INLINE_FRAGMENT = "INLINE_FRAGMENT"


_T = t.TypeVar("_T")


class DirectiveField(dataclasses.Field, t.Generic[_T]):
    def __init__(
        self,
        name: t.Optional[str] = None,
        description: str = "",
        default_value: t.Any = dataclasses.MISSING,
    ):
        kwargs: t.Dict[str, t.Any] = {}

        if sys.version_info >= (3, 10):
            kwargs["kw_only"] = False

        super().__init__(
            default=default_value,
            default_factory=dataclasses.MISSING,  # type: ignore
            init=True,
            repr=True,
            compare=True,
            hash=None,
            metadata={},
            **kwargs,
        )

        self.field_name = name
        self.type_ident = None
        self.description = description
        self.default_value = (
            None if default_value is dataclasses.MISSING else default_value
        )


def directive_field(
    name: t.Optional[str] = None,
    description: str = "",
    default_value: t.Any = dataclasses.MISSING,
) -> t.Any:  # note: t.Any is a workaround for mypy
    return DirectiveField(name, description, default_value)


@dataclass
class DirectiveInfo:
    name: str
    locations: t.List[Location]
    args: t.List[DirectiveField]
    description: t.Optional[str] = None
    repeatable: bool = False


class Directive:
    """Base class for all operation directives."""

    __directive_info__: t.Any  # DirectiveInfo

    @classmethod
    def args_map(cls) -> OrderedDict:
        return OrderedDict(
            (arg.name, arg) for arg in cls.__directive_info__.args
        )

    def accept(self, visitor: t.Any) -> t.Any:
        return visitor.visit_directive(self)


@dataclass_transform(field_specifiers=(DirectiveField,))
def directive(
    *,
    name: str,
    locations: t.List[Location],
    description: t.Optional[str] = None,
    repeatable: bool = False,
) -> t.Callable:
    """Decorator to mark class as operation directive.
    A class with a @directive decorator will become a dataclass.
    """
    # TODO: validation locations

    def _wrap(cls: T) -> T:
        cls = t.cast(T, wrap_dataclass(cls))
        fields = get_fields(cls, DirectiveField)
        for field in fields:
            field.type_ident = builtin_to_introspection_type(field.type)
            field.field_name = field.field_name or field.name

        cls.__directive_info__ = DirectiveInfo(
            name=name,
            locations=locations,
            args=fields,
            description=description,
            repeatable=repeatable,
        )

        def __hash(self, *args, **kwargs) -> int:  # type: ignore[no-untyped-def]  # noqa: E501
            return hash(cls.__directive_info__.name)

        cls.__hash__ = __hash  # type: ignore[assignment]

        return cls

    return _wrap


@directive(
    name="cached",
    locations=[
        Location.FIELD,
        Location.FRAGMENT_SPREAD,
        Location.INLINE_FRAGMENT,
    ],
    description="Caches node and all its fields",
)
class Cached(Directive):
    ttl: int = directive_field(
        description="How long field will live in cache.",
    )


# Internal directive
@directive(
    name="skip",
    locations=[
        Location.FIELD,
        Location.FRAGMENT_SPREAD,
        Location.INLINE_FRAGMENT,
    ],
    description=(
        "Directs the executor to skip this field or fragment "
        "when the `if` argument is true."
    ),
)
class _SkipDirective(Directive):
    if_: bool = directive_field(
        name="if",
        description="Skipped when true.",
    )


@directive(
    name="include",
    locations=[
        Location.FIELD,
        Location.FRAGMENT_SPREAD,
        Location.INLINE_FRAGMENT,
    ],
    description=(
        "Directs the executor to include this field or fragment "
        "only when the `if` argument is true."
    ),
)
class _IncludeDirective(Directive):
    if_: bool = directive_field(
        name="if",
        description="Included when true.",
    )


class SchemaDirectiveField(dataclasses.Field, t.Generic[_T]):
    def __init__(
        self,
        name: t.Optional[str] = None,
        description: str = "",
        default_value: t.Any = dataclasses.MISSING,
    ):
        kwargs: t.Dict[str, t.Any] = {}

        if sys.version_info >= (3, 10):
            kwargs["kw_only"] = False

        super().__init__(
            default=default_value,
            default_factory=dataclasses.MISSING,  # type: ignore
            init=True,
            repr=True,
            compare=True,
            hash=None,
            metadata={},
            **kwargs,
        )

        self.field_name = name
        self.type_ident = None
        self.description = description
        self.default_value = (
            None if default_value is dataclasses.MISSING else default_value
        )


def schema_directive_field(
    name: t.Optional[str] = None,
    description: str = "",
    default_value: t.Any = dataclasses.MISSING,
) -> t.Any:  # note: t.Any is a workaround for mypy
    return SchemaDirectiveField(name, description, default_value)


@dataclass
class SchemaDirectiveInfo:
    name: str
    locations: t.List[Location]
    args: t.List[SchemaDirectiveField]
    description: t.Optional[str] = None
    repeatable: bool = False


@dataclass_transform(field_specifiers=(SchemaDirectiveField,))
def schema_directive(
    *,
    name: str,
    locations: t.List[Location],
    description: t.Optional[str] = None,
    repeatable: bool = False,
) -> t.Callable:
    """Decorator to mark class as schema directive.
    A class with a @schema_directive decorator will become a dataclass.
    """

    def _wrap(cls: T) -> T:
        cls = t.cast(T, wrap_dataclass(cls))
        fields = get_fields(cls, SchemaDirectiveField)
        for field in fields:
            field.type_ident = builtin_to_introspection_type(field.type)
            field.field_name = field.field_name or field.name

        cls.__directive_info__ = SchemaDirectiveInfo(
            name=name,
            locations=locations,
            args=fields,
            description=description,
            repeatable=repeatable,
        )

        def __hash(self, *args, **kwargs) -> int:  # type: ignore[no-untyped-def]  # noqa: E501
            return hash(cls.__directive_info__.name)

        cls.__hash__ = __hash  # type: ignore[assignment]

        return cls

    return _wrap


class SchemaDirective:
    """Base class for all schema directives."""

    __directive_info__: t.Any  # SchemaDirectiveInfo

    @classmethod
    def args_map(cls) -> OrderedDict:
        return OrderedDict(
            (arg.name, arg) for arg in cls.__directive_info__.args
        )

    def accept(self, visitor: t.Any) -> t.Any:
        return visitor.visit_schema_directive(self)


@schema_directive(
    name="deprecated",
    locations=[Location.FIELD_DEFINITION, Location.ENUM_VALUE],
    description="Marks the field or enum value as deprecated",
)
class Deprecated(SchemaDirective):
    """https://spec.graphql.org/June2018/#sec--deprecated"""

    reason: t.Optional[str] = schema_directive_field(
        description="Deprecation reason.",
        default_value=None,
    )


def get_deprecated(field: t.Union["Field", "Link"]) -> t.Optional[Deprecated]:
    """Get deprecated directive"""
    return next(
        (d for d in field.directives if isinstance(d, Deprecated)), None
    )
