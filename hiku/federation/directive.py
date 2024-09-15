from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, List, Optional, TypeVar
from typing_extensions import dataclass_transform

from hiku.directives import (
    SchemaDirectiveInfo,
    Location,
    SchemaDirective,
    SchemaDirectiveField,
    schema_directive_field,
    get_fields,
    wrap_dataclass,
)
from hiku.federation.scalars import FieldSet, LinkImport
from hiku.utils.typing import builtin_to_introspection_type

T = TypeVar("T", bound="FederationSchemaDirective")


LinkPurpose = Enum("link__Purpose", ["SECURITY", "EXECUTION"])  # type: ignore[misc]  # noqa: E501


@dataclass
class ComposeOptions:
    import_url: Optional[str]


@dataclass
class FederationSchemaDirectiveInfo(SchemaDirectiveInfo):
    compose_options: Optional[ComposeOptions] = None


@dataclass_transform(field_specifiers=(SchemaDirectiveField,))
def schema_directive(
    *,
    name: str,
    locations: List[Location],
    description: Optional[str] = None,
    repeatable: bool = False,
    compose: bool = False,
    import_url: Optional[str] = None,
) -> Callable[..., T]:
    """Decorator to mark class as federated schema directive.
    A class with a @schema_directive decorator will become a dataclass.

    :param compose: If True, the directive will be added to the schema
        and will be wrapped in @composeDirective
        See: https://www.apollographql.com/docs/federation/federated-types/federated-directives#composedirective  # noqa: E501
    :param import_url: The URL of the subgraph that defines the directive.
        See: https://specs.apollo.dev/link/v1.0/#@link.url
    """

    def _wrap(cls: T) -> T:
        if not issubclass(cls, FederationSchemaDirective):  # type: ignore[arg-type]  # noqa: E501
            raise TypeError(
                f"{cls} is not a subclass of {FederationSchemaDirective}"
            )

        cls = wrap_dataclass(cls)  # type: ignore[arg-type, assignment]
        fields = get_fields(cls, SchemaDirectiveField)  # type: ignore[arg-type]
        for field in fields:
            field.type_ident = builtin_to_introspection_type(field.type)
            field.field_name = field.field_name or field.name

        cls.__directive_info__ = FederationSchemaDirectiveInfo(
            name=name,
            locations=locations,
            args=fields,
            description=description,
            repeatable=repeatable,
            compose_options=(
                ComposeOptions(import_url=import_url) if compose else None
            ),
        )

        return cls

    return _wrap


class FederationSchemaDirective(SchemaDirective):
    """Base class for federation directives"""

    __directive_info__: Any  # FederationSchemaDirectiveInfo


# v1/v2 directives
@schema_directive(
    name="key",
    locations=[Location.OBJECT, Location.INTERFACE],
    description=(
        "The @key directive is used to indicate a combination "
        "of fields that can be used to uniquely identify and "
        "fetch an object or interface."
    ),
    repeatable=True,
)
class Key(FederationSchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federated-types/federated-directives#key
    """

    fields: FieldSet = schema_directive_field(
        description=(
            "A combination of fields that can be used to uniquely "
            "identify and fetch an object or interface"
        ),
    )
    resolvable: bool = schema_directive_field(
        description="",
        default_value=True,
    )


@schema_directive(
    name="provides",
    locations=[Location.FIELD_DEFINITION],
    description=(
        "The @provides directive is used to annotate the expected returned "
        "fieldset from a field on a base type that is guaranteed to be "
        "selectable by the gateway"
    ),
)
class Provides(FederationSchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#provides
    """

    fields: FieldSet = schema_directive_field(
        description=(
            "Expected returned fieldset from a field on a base type "
            "that is guaranteed to be selectable by the gateway"
        ),
    )


@schema_directive(
    name="requires",
    locations=[Location.FIELD_DEFINITION],
    description=(
        "The @requires directive is used to annotate the required input "
        "fieldset from a base type for a resolver."
    ),
)
class Requires(FederationSchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#requires
    """

    fields: FieldSet = schema_directive_field(
        description=(
            "The required input fieldset from a base type for a " "resolver"
        ),
    )


@schema_directive(
    name="external",
    locations=[Location.FIELD_DEFINITION, Location.OBJECT],
    description=(
        "The @external directive is used to mark a field "
        "as owned by another service."
    ),
)
class External(FederationSchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#external
    """


@schema_directive(
    name="extends",
    locations=[Location.OBJECT, Location.INTERFACE],
    description=(
        "Indicates that an object or interface definition "
        "is an extension of another definition of that same type. "
    ),
)
class Extends(FederationSchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federated-types/federated-directives#extends

    NOTE: This directive is not exposed in introspection and sdl, and used to
    specify that a type is an extension of another type.
    Apollo recommends to use `extend type` instead of @extends directive.
    """


# v2 directives
@schema_directive(
    name="tag",
    locations=[
        Location.FIELD_DEFINITION,
        Location.INTERFACE,
        Location.OBJECT,
        Location.UNION,
        Location.ARGUMENT_DEFINITION,
        Location.SCALAR,
        Location.ENUM,
        Location.ENUM_VALUE,
        Location.INPUT_OBJECT,
        Location.INPUT_FIELD_DEFINITION,
    ],
    description="Applies arbitrary string metadata to a schema location",
    repeatable=True,
)
class Tag(FederationSchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federated-types/federated-directives#tag
    """

    name: str = schema_directive_field(
        description="The tag name to apply",
    )


@schema_directive(
    name="override",
    locations=[Location.FIELD_DEFINITION],
    description=(
        "Indicates that an object or interface definition "
        "is an extension of another definition of that same type. "
    ),
)
class Override(FederationSchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federated-types/federated-directives#override
    """

    from_: str = schema_directive_field(
        "from",
        description=(
            "The name of the other subgraph that no longer "
            "resolves the field"
        ),
    )


@schema_directive(
    name="inaccessible",
    locations=[
        Location.FIELD_DEFINITION,
        Location.INTERFACE,
        Location.OBJECT,
        Location.UNION,
        Location.ARGUMENT_DEFINITION,
        Location.SCALAR,
        Location.ENUM,
        Location.ENUM_VALUE,
        Location.INPUT_OBJECT,
        Location.INPUT_FIELD_DEFINITION,
    ],
    description=(
        "Indicates that a definition in the subgraph schema "
        "should be omitted from the router's API schema, "
        "even if that definition is also present in other subgraphs"
    ),
)
class Inaccessible(FederationSchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federated-types/federated-directives#inaccessible
    """


@schema_directive(
    name="shareable",
    locations=[
        Location.FIELD_DEFINITION,
        Location.OBJECT,
    ],
    description=(
        "Indicates that an object type's field is allowed "
        "to be resolved by multiple subgraphs"
    ),
)
class Shareable(FederationSchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federated-types/federated-directives#shareable
    """


@schema_directive(
    name="interfaceObject",
    locations=[
        Location.OBJECT,
    ],
    description=(
        "Indicates that an object definition serves "
        "as an abstraction of another subgraph's entity interface. "
    ),
)
class InterfaceObject(FederationSchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federated-types/federated-directives#interfaceobject
    """


@schema_directive(
    name="composeDirective",
    locations=[
        Location.SCHEMA,
    ],
    description=(
        "Indicates to composition that all uses of a "
        "particular custom type system directive in the "
        "subgraph schema should be preserved in the supergraph schema"
    ),
    repeatable=True,
)
class ComposeDirective(FederationSchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federated-types/federated-directives#composedirective
    """

    name: str = schema_directive_field(
        description="The name (including the leading @) of the "
        "directive to preserve during composition.",
    )


@schema_directive(
    name="link",
    locations=[Location.SCHEMA],
    description=(
        "Indicates to composition that all uses of a "
        "particular custom type system directive in the "
        "subgraph schema should be preserved in the supergraph schema"
    ),
    repeatable=True,
)
class Link(FederationSchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federated-types/federated-directives#the-link-directive
    """

    url: str = schema_directive_field()
    as_: Optional[str] = schema_directive_field(
        "as",
        default_value=None,
    )
    for_: Optional[LinkPurpose] = schema_directive_field(
        "for",
        default_value=None,
    )
    import_: Optional[List[Optional[LinkImport]]] = schema_directive_field(
        "import",
        default_value=None,
    )
