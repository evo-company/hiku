from hiku.directives import Location, SchemaDirective, Argument
from hiku.introspection.types import NON_NULL, SCALAR


class Key(SchemaDirective):
    """
    https://www.apollographql.com/docs/federation/v1/federation-spec#key
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
    https://www.apollographql.com/docs/federation/v1/federation-spec#provides
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
    https://www.apollographql.com/docs/federation/v1/federation-spec#requires
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
    https://www.apollographql.com/docs/federation/v1/federation-spec#external
    """
    name = 'external'
    locations = [Location.FIELD_DEFINITION]
    args = []
    description=(
        'The @external directive is used to mark a field '
        'as owned by another service.'
    )
    repeatable = False


class Extends(SchemaDirective):
    """
    https://www.apollographql.com/docs/federation/v1/federation-spec/#federation-schema-specification

    NOTE: This directive is not exposed in introspection and sdl, and used to
    specify that a type is an extension of another type.
    Apollo recommends to use extend type instead of @extends directive.
    """
    name = 'extends'
    locations = [Location.OBJECT, Location.INTERFACE]
    args = []
    description = (
        'Indicates that an object or interface definition '
        'is an extension of another definition of that same type. '
    )
    repeatable = False
