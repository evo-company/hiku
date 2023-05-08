import dataclasses
import sys
import typing as t

from collections import OrderedDict
from dataclasses import dataclass
from typing import TYPE_CHECKING
from enum import Enum

from hiku.introspection.types import NON_NULL, SCALAR

if TYPE_CHECKING:
    from hiku.graph import Field, Link


_T = t.TypeVar("_T")


def wrap_dataclass(cls: t.Type):
    dclass_kwargs: t.Dict[str, bool] = {}
    dclass = dataclasses.dataclass(cls, **dclass_kwargs)

    return dclass


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


class DirectiveField(dataclasses.Field):
    def __init__(
        self,
        name: str,
        type_ident: t.Any,  # hiku.introspection.types.*
        description: str = "",
        default_value: t.Any = dataclasses.MISSING
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

        # name attribute is used by dataclasses.Field
        self.field_name = name
        # TODO: infer typeident from annotations
        self.type_ident = type_ident
        self.description = description
        self.default_value = None if default_value is dataclasses.MISSING else default_value


@dataclass
class DirectiveInfo:
    name: str
    locations: t.List[Location]
    args: t.List[DirectiveField]
    description: t.Optional[str] = None
    repeatable: bool = False


T = t.TypeVar("T", bound=t.Type)


def get_fields(cls: T) -> t.List[DirectiveField]:
    fields = []
    for field in dataclasses.fields(cls):
        if isinstance(field, DirectiveField):
            fields.append(field)

    return fields


def schema_directive(
    *,
    name: str,
    locations: t.List[Location],
    description: t.Optional[str] = None,
    repeatable: bool = False
) -> t.Callable:
    """Decorator to mark class as schema directive.
    A class with a @schema_directive decorator will become a dataclass.
    """
    def _wrap(cls: T) -> T:
        cls = wrap_dataclass(cls)
        fields = get_fields(cls)
        cls.__directive_info__ = DirectiveInfo(
            name=name,
            locations=locations,
            args=fields,
            description=description,
            repeatable=repeatable,
        )
        cls.__hash__ = lambda self: hash(cls.__directive_info__.name)

        return cls

    return _wrap


class SchemaDirective:
    __directive_info__: t.ClassVar[DirectiveInfo]

    @classmethod
    def args_map(cls):
        return OrderedDict((arg.name, arg) for arg in cls.__directive_info__.args)

    def accept(self, visitor: t.Any) -> t.Any:
        return visitor.visit_directive(self)


@schema_directive(
    name="deprecated",
    locations=[Location.FIELD_DEFINITION, Location.ENUM_VALUE],
    description='Marks the field or enum value as deprecated',
)
class Deprecated(SchemaDirective):
    """https://spec.graphql.org/June2018/#sec--deprecated"""
    reason: t.Optional[str] = DirectiveField(
        name='reason',
        type_ident=SCALAR("String"),
        description='Deprecation reason.',
        default_value=None,
    )


def get_deprecated(field: t.Union["Field", "Link"]) -> t.Optional[Deprecated]:
    """Get deprecated directive"""
    return next((d for d in field.directives if isinstance(d, Deprecated)), None)


@schema_directive(
    name="cached",
    locations=[Location.FIELD, Location.FRAGMENT_SPREAD, Location.INLINE_FRAGMENT],
    description="Caches node and all its fields",
)
class Cached(SchemaDirective):
    ttl: int = DirectiveField(
        name="ttl",
        type_ident=NON_NULL(SCALAR("Int")),
        description="How long field will live in cache.",
    )


# Internal directive
@schema_directive(
    name="skip",
    locations=[Location.FIELD, Location.FRAGMENT_SPREAD, Location.INLINE_FRAGMENT],
    description=(
        "Directs the executor to skip this field or fragment "
        "when the `if` argument is true."
    )
)
class _SkipDirective(SchemaDirective):
    if_: bool = DirectiveField(
        name="if",
        type_ident=NON_NULL(SCALAR("Boolean")),
        description="Skipped when true.",
    )


# Internal directive
@schema_directive(
    name="include",
    locations=[Location.FIELD, Location.FRAGMENT_SPREAD, Location.INLINE_FRAGMENT],
    description=(
            "Directs the executor to include this field or fragment "
            "only when the `if` argument is true."
    )
)
class _IncludeDirective(SchemaDirective):
    if_: bool = DirectiveField(
        name="if",
        type_ident=NON_NULL(SCALAR("Boolean")),
        description="Included when true.",
    )
