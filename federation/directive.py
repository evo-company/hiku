from typing import (
    List,
    Dict,
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
    """https://www.apollographql.com/docs/federation/federation-spec/#key"""
    @property
    def name(self) -> str:
        return 'key'

    @property
    def locations(self) -> List[str]:
        return ['OBJECT', 'INTERFACE']

    @property
    def description(self) -> str:
        return (
            'The @key directive is used to indicate a combination '
            'of fields that can be used to uniquely identify and '
            'fetch an object or interface.'
        )

    @property
    def args(self) -> Dict[str, Arg]:
        return {
            'fields': Arg(
                description='',
                type=NON_NULL(SCALAR('String'))
            )
        }


class ProvidesDirective(Directive):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#provides
    """
    @property
    def name(self) -> str:
        return 'provides'

    @property
    def locations(self) -> List[str]:
        return ['FIELD_DEFINITION']

    @property
    def description(self) -> str:
        return (
            'The @provides directive is used to annotate the expected returned '
            'fieldset from a field on a base type that is guaranteed to be '
            'selectable by the gateway'
        )

    @property
    def args(self) -> Dict[str, Arg]:
        return {
            'fields': Arg(
                description='',
                type=NON_NULL(SCALAR('String'))
            )
        }


class RequiresDirective(Directive):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#requires
    """
    @property
    def name(self) -> str:
        return 'requires'

    @property
    def locations(self) -> List[str]:
        return ['FIELD_DEFINITION']

    @property
    def description(self) -> str:
        return (
            'The @requires directive is used to annotate the required input '
            'fieldset from a base type for a resolver.'
        )

    @property
    def args(self) -> Dict[str, Arg]:
        return {
            'fields': Arg(
                description='',
                type=NON_NULL(SCALAR('String'))
            )
        }


class ExternalDirective(Directive):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#external
    """
    @property
    def name(self) -> str:
        return 'external'

    @property
    def locations(self) -> List[str]:
        return ['FIELD_DEFINITION']

    @property
    def description(self) -> str:
        return (
            'The @external directive is used to mark a field '
            'as owned by another service.'
        )

    @property
    def args(self) -> Dict[str, Arg]:
        return {
            'fields': Arg(
                description='',
                type=NON_NULL(SCALAR('String'))
            )
        }
