import typing as t

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from enum import Enum

from hiku.introspection.types import NON_NULL, SCALAR

if TYPE_CHECKING:
    from hiku.graph import Field, Link


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
    QUERY = 'QUERY'
    MUTATION = 'MUTATION'
    SUBSCRIPTION = 'SUBSCRIPTION'
    FIELD = 'FIELD'
    FRAGMENT_DEFINITION = 'FRAGMENT_DEFINITION'
    FRAGMENT_SPREAD = 'FRAGMENT_SPREAD'
    INLINE_FRAGMENT = 'INLINE_FRAGMENT'


@dataclass(frozen=True)
class Argument:
    name: str
    type_ident: t.Any  # hiku.introspection.types.*
    description: str
    default_value: t.Any


@dataclass
class SchemaDirective:
    """TODO: describe how to create custom directives"""
    name: str = field(init=False)
    locations: t.List[Location] = field(init=False)
    args: t.List[Argument] = field(init=False)
    description: t.Optional[str] = field(init=False)
    repeatable: bool = field(init=False, default=False)
    """this is where we store input arguments"""
    input_args: t.Dict[str, t.Any] = field(init=False)

    def __init__(self, **kwargs):
        """__init__ accepts only keyword arguments
        so we can validate and store them in input_args dict
        """
        self.input_args = {}
        for arg in self.args:
            value = kwargs.pop(arg.name, None)
            if value is None:
                if isinstance(arg.type_ident, NON_NULL):
                    raise ValueError(
                        f'Argument {arg.name} is required for directive '
                        f'{self.name}'
                    )
                value = arg.default_value
            self.input_args[arg.name] = value

    @classmethod
    def args_map(cls):
        return OrderedDict((arg.name, arg) for arg in cls.args)

    def accept(self, visitor: t.Any) -> t.Any:
        return visitor.visit_directive(self)


class Deprecated(SchemaDirective):
    """
    https://spec.graphql.org/June2018/#sec--deprecated
    """
    name = 'deprecated'
    locations = [Location.FIELD_DEFINITION, Location.ENUM_VALUE]
    args = [
        Argument(
            name='reason',
            type_ident=SCALAR("String"),
            description='Deprecation reason.',
            default_value=None,
        ),
    ]
    description = 'Marks the field or enum value as deprecated'
    repeatable = False

    def __init__(self, reason: t.Optional[str] = None):
        super().__init__(reason=reason)


def get_deprecated(field: t.Union['Field', 'Link']) -> t.Optional[Deprecated]:
    """Get deprecated directive"""
    return next(
        (d for d in field.directives if isinstance(d, Deprecated)),
        None
    )


class Cached(SchemaDirective):
    name = 'cached'
    locations = [
        Location.FIELD, Location.FRAGMENT_SPREAD, Location.INLINE_FRAGMENT
    ]
    args = [
        Argument(
            name='ttl',
            type_ident=NON_NULL(SCALAR('Int')),
            description='How long field will live in cache.',
            default_value=None,
        ),
    ]
    description='Caches node and all its fields'
    repeatable = False


# Internal directive
class _SkipDirective(SchemaDirective):
    name = 'skip'
    locations = [
        Location.FIELD, Location.FRAGMENT_SPREAD, Location.INLINE_FRAGMENT
    ]
    args = [
        Argument(
            name='if',
            type_ident=NON_NULL(SCALAR('Boolean')),
            description='Skipped when true.',
            default_value=None,
        ),
    ]
    description=(
        'Directs the executor to skip this field or fragment '
        'when the `if` argument is true.'
    )
    repeatable = False


# Internal directive
class _IncludeDirective(SchemaDirective):
    name = 'include'
    locations = [
        Location.FIELD, Location.FRAGMENT_SPREAD, Location.INLINE_FRAGMENT
    ]
    args = [
        Argument(
            name='if',
            type_ident=NON_NULL(SCALAR('Boolean')),
            description='Included when true.',
            default_value=None,
        ),
    ]
    description=(
        'Directs the executor to include this field or fragment '
        'only when the `if` argument is true.'
    )
