from typing import (
    List,
    Optional,
)

from hiku.introspection.directive import (
    Directive,
    Arg,
)
from hiku.introspection.types import (
    SCALAR,
    NON_NULL,
)


class KeyDirective(Directive):
    # key is a key arg with value
    def __init__(self, key: Optional[str] = None):
        self._args = [
            Arg(
                name='fields',
                description='',
                type=NON_NULL(SCALAR('String')), # TODO maybe use here different type ? Such as Optional[String]
                 # Because we already know how to encode it
                value=key
            )
        ]

    """https://www.apollographql.com/docs/federation/federation-spec/#key"""
    name = 'key'
    locations = ['OBJECT', 'INTERFACE']
    description = (
        'The @key directive is used to indicate a combination '
        'of fields that can be used to uniquely identify and '
        'fetch an object or interface.'
    )

    @property
    def args(self) -> List[Arg]:
        return self._args


class ProvidesDirective(Directive):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#provides
    """
    name = 'provides'
    locations = ['FIELD_DEFINITION']
    description = (
        'The @provides directive is used to annotate the expected returned '
        'fieldset from a field on a base type that is guaranteed to be '
        'selectable by the gateway'
    )

    @property
    def args(self) -> List[Arg]:
        return [
            Arg(
                name='fields',
                description='',
                type=NON_NULL(SCALAR('String')),
                value=None
            )
        ]


class RequiresDirective(Directive):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#requires
    """
    name = 'requires'
    locations = ['FIELD_DEFINITION']
    description = (
        'The @requires directive is used to annotate the required input '
        'fieldset from a base type for a resolver.'
    )

    @property
    def args(self) -> List[Arg]:
        return [
            Arg(
                name='fields',
                description='',
                type=NON_NULL(SCALAR('String')),
                value=None
            )
        ]


class ExternalDirective(Directive):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#external
    """
    name = 'external'
    locations = ['external']
    description = (
        'The @external directive is used to mark a field '
        'as owned by another service.'
    )

    @property
    def args(self) -> List[Arg]:
        return []

