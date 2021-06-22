from collections import OrderedDict
from typing import (
    List,
    NamedTuple,
    Dict,
    Any,
)

from abc import ABC, abstractmethod

from hiku.introspection.types import (
    NON_NULL,
    SCALAR,
)


from hiku.utils import cached_property


class Arg(NamedTuple):
    name: str
    value: Any
    description: str
    type: Any


class Directive(ABC):
    name: str
    locations: List[str]
    description: str

    @property
    @abstractmethod
    def args(self) -> List[Arg]:
        """Directive arguments"""
        pass

    @cached_property
    def args_map(self) -> 'OrderedDict[str, Arg]':
        return OrderedDict((arg.name, arg) for arg in self.args)

    def value_info(self, fields):
        info = {'name': self.name,
                'description': self.description,
                'locations': self.locations}
        yield [info[f.name] for f in fields]


class IncludeDirective(Directive):
    name = 'include'
    locations = ['FIELD', 'FRAGMENT_SPREAD', 'INLINE_FRAGMENT']
    description = (
        'Directs the executor to include this field or fragment '
        'only when the `if` argument is true.'
    )

    @property
    def args(self) -> List[Arg]:
        return [
            Arg(
                name='if',
                description='Included when true.',
                type=NON_NULL(SCALAR('Boolean')),
                value=None
            )
        ]


class SkipDirective(Directive):
    name = 'skip'
    locations = ['FIELD', 'FRAGMENT_SPREAD', 'INLINE_FRAGMENT']
    description = (
        'Directs the executor to skip this field or fragment '
        'when the `if` argument is true.'
    )

    @property
    def args(self) -> List[Arg]:
        return [
            Arg(
                name='if',
                description='Skipped when true.',
                type=NON_NULL(SCALAR('Boolean')),
                value=None
            )
        ]


def get_default_directives():
    return [
        SkipDirective(),
        IncludeDirective(),
    ]
