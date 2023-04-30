from typing import Optional

from hiku.directives import Location, SchemaDirective, Argument
from hiku.introspection.types import NON_NULL, SCALAR


class Key(SchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federated-types/federated-directives#key
    """
    name = 'key'
    locations = [Location.OBJECT, Location.INTERFACE]
    args = [
        Argument(
            name='fields',
            type_ident=NON_NULL(SCALAR('_FieldSet')),
            description=(
                'A combination of fields that can be used to uniquely '
                'identify and fetch an object or interface'
            ),
            default_value=None,
        ),
    ]
    description=(
        'The @key directive is used to indicate a combination '
        'of fields that can be used to uniquely identify and '
        'fetch an object or interface.'
    )
    repeatable = True

    def __init__(self, fields: str, resolvable: bool = True) -> None:
        super().__init__(fields=fields, resolvable=resolvable)


class Provides(SchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#provides
    """
    name = 'provides'
    locations = [Location.FIELD_DEFINITION]
    args = [
        Argument(
            name='fields',
            type_ident=NON_NULL(SCALAR('_FieldSet')),
            description=(
                'Expected returned fieldset from a field on a base type '
                'that is guaranteed to be selectable by the gateway'
            ),
            default_value=None,
        ),
    ]
    description=(
        'The @provides directive is used to annotate the expected returned '
        'fieldset from a field on a base type that is guaranteed to be '
        'selectable by the gateway'
    )
    repeatable = False

    def __init__(self, fields: str) -> None:
        super().__init__(fields=fields)


class Requires(SchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#requires
    """
    name = 'requires'
    locations = [Location.FIELD_DEFINITION]
    args = [
        Argument(
            name='fields',
            type_ident=NON_NULL(SCALAR('_FieldSet')),
            description=(
                'The required input fieldset from a base type for a '
                'resolver'
            ),
            default_value=None,
        ),
    ]
    description=(
        'The @requires directive is used to annotate the required input '
        'fieldset from a base type for a resolver.'
    )
    repeatable = False

    def __init__(self, fields: str) -> None:
        super().__init__(fields=fields)


class External(SchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#external
    """
    name = 'external'
    locations = [Location.FIELD_DEFINITION, Location.OBJECT]
    args = []
    description=(
        'The @external directive is used to mark a field '
        'as owned by another service.'
    )
    repeatable = False


class Extends(SchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federated-types/federated-directives#extends

    NOTE: This directive is not exposed in introspection and sdl, and used to
    specify that a type is an extension of another type.
    Apollo recommends to use extend type instead of @extends directive.
    """
    name = 'extends'
    locations = [Location.OBJECT, Location.INTERFACE]
    args = []
    description=(
        'Indicates that an object or interface definition '
        'is an extension of another definition of that same type. '
    )
    repeatable = False


class Tag(SchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federated-types/federated-directives#tag
    """
    name = 'tag'
    locations = [
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
    ]
    args = [
        Argument(
            name='name',
            type_ident=NON_NULL(SCALAR('String')),
            description='The tag name to apply',
            default_value=None,
        ),
    ]
    description='Applies arbitrary string metadata to a schema location'
    repeatable = True

    def __init__(self, name: str) -> None:
        super().__init__(name=name)


class Override(SchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federated-types/federated-directives#override
    """
    name = 'override'
    locations = [Location.FIELD_DEFINITION]
    args = [
        Argument(
            name='from',
            type_ident=NON_NULL(SCALAR('String')),
            description='The name of the other subgraph that no longer '
                        'resolves the field',
            default_value=None,
        ),
    ]
    description=(
        'Indicates that an object or interface definition '
        'is an extension of another definition of that same type. '
    )
    repeatable = False

    def __init__(self, from_: str) -> None:
        super().__init__(from_=from_)


class Inaccessible(SchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federated-types/federated-directives#inaccessible
    """
    name = 'inaccessible'
    locations = [
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
    ]
    args = []
    description=(
        "Indicates that a definition in the subgraph schema "
        "should be omitted from the router's API schema, "
        "even if that definition is also present in other subgraphs"
    )
    repeatable = False


class Shareable(SchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federated-types/federated-directives#shareable
    """
    name = 'shareable'
    locations = [Location.FIELD_DEFINITION, Location.OBJECT]
    args = []
    description=(
        "Indicates that an object type's field is allowed "
        "to be resolved by multiple subgraphs"
    )
    repeatable = False


class InterfaceObject(SchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federated-types/federated-directives#interfaceobject
    """
    name = 'interfaceObject'
    locations = [Location.OBJECT]
    args = []
    description=(
        "Indicates that an object definition serves "
        "as an abstraction of another subgraph's entity interface. "
    )
    repeatable = False


class ComposeDirective(SchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federated-types/federated-directives#composedirective
    """
    name = 'composeDirective'
    locations = [Location.SCHEMA]
    args = [
        Argument(
            name='name',
            type_ident=NON_NULL(SCALAR('String')),
            description='The name (including the leading @) of the '
                        'directive to preserve during composition.',
            default_value=None,
        ),
    ]
    description=(
        "Indicates to composition that all uses of a "
        "particular custom type system directive in the "
        "subgraph schema should be preserved in the supergraph schema"
    )
    repeatable = True

    def __init__(self, name: str) -> None:
        super().__init__(name=name)


class Link(SchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federated-types/federated-directives#the-link-directive
    """
    name = 'link'
    locations = [Location.SCHEMA]
    args = [
        Argument(
            name='url',
            type_ident=NON_NULL(SCALAR('String')),
            description='',
            default_value=None,
        ),
        Argument(
            name='as',
            type_ident=SCALAR('String'),
            description='',
            default_value=None,
        ),
        Argument(
            name='for',
            type_ident=SCALAR('link__Purpose'),  # TODO: this type ???
            description='',
            default_value=None,
        ),
        Argument(
            name='import',
            type_ident=SCALAR('[link__Import]'),  # TODO: this type ???
            description='',
            default_value=None,
        ),
    ]
    description=(
        "Indicates to composition that all uses of a "
        "particular custom type system directive in the "
        "subgraph schema should be preserved in the supergraph schema"
    )
    repeatable = True

    def __init__(
        self,
        url: str,
        as_: Optional[str] = None,
        for_: Optional[str] = None,
        import_: Optional[str] = None,
    ) -> None:
        super().__init__(**{
            'url': url,
            'as': as_,
            'for': for_,
            'import': import_,
        })
