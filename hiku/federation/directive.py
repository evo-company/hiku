from hiku.directives import SchemaDirective, DirectiveMeta
from hiku.introspection.types import (
    NON_NULL,
    SCALAR,
)


class Key(SchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#key
    """
    meta = DirectiveMeta(
        name='key',
        locations=['OBJECT', 'INTERFACE'],
        description=(
            'The @key directive is used to indicate a combination '
            'of fields that can be used to uniquely identify and '
            'fetch an object or interface.'
        ),
        args=[
            DirectiveMeta.Arg(
                name='fields',
                type_ident=NON_NULL(SCALAR('_FieldSet')),
                description=(
                    'A combination of fields that can be used to uniquely '
                    'identify and fetch an object or interface'
                ),
                default_value=None,
            ),
        ],
    )

    def __init__(self, fields: str) -> None:
        self.fields = fields


class Provides(SchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#provides
    """
    meta = DirectiveMeta(
        name='provides',
        locations=['FIELD_DEFINITION'],
        description=(
            'The @provides directive is used to annotate the expected returned '
            'fieldset from a field on a base type that is guaranteed to be '
            'selectable by the gateway'
        ),
        args=[
            DirectiveMeta.Arg(
                name='fields',
                type_ident=NON_NULL(SCALAR('_FieldSet')),
                description=(
                    'Expected returned fieldset from a field on a base type '
                    'that is guaranteed to be selectable by the gateway'
                ),
                default_value=None,
            ),
        ],
    )

    def __init__(self, fields: str) -> None:
        self.fields = fields


class Requires(SchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#requires
    """
    meta = DirectiveMeta(
        name='requires',
        locations=['FIELD_DEFINITION'],
        description=(
            'The @requires directive is used to annotate the required input '
            'fieldset from a base type for a resolver.'
        ),
        args=[
            DirectiveMeta.Arg(
                name='fields',
                type_ident=NON_NULL(SCALAR('_FieldSet')),
                description=(
                    'The required input fieldset from a base type for a '
                    'resolver'
                ),
                default_value=None,
            ),
        ],
    )

    def __init__(self, fields: str) -> None:
        self.fields = fields


class External(SchemaDirective):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#external
    """
    meta = DirectiveMeta(
        name='external',
        locations=['FIELD_DEFINITION'],
        description=(
            'The @external directive is used to mark a field '
            'as owned by another service.'
        ),
        args=[],
    )


class Extends(SchemaDirective):
    """
    Apollo Federation supports using an @extends directive in place of extend
    type to annotate type references
    https://www.apollographql.com/docs/federation/federation-spec/
    """
    meta = DirectiveMeta(
        name='extends',
        locations=['OBJECT', 'INTERFACE'],
        description=(
            'The @extends directive is used to mark a field '
            'that can extend some type in other service.'
        ),
        args=[],
    )
