from collections import OrderedDict
from typing import (
    List,
    NamedTuple,
    Any,
)

from abc import ABC, abstractmethod

from hiku.types import (
    Boolean,
    GenericMeta,
)
from hiku.utils import cached_property


class Arg(NamedTuple):
    name: str
    value: Any
    description: str
    type: GenericMeta


class Directive(ABC):
    name: str
    locations: List[str]
    description: str

    @property
    @abstractmethod
    def args(self) -> List[Arg]:
        """Directive arguments"""

    @cached_property
    def args_map(self) -> 'OrderedDict[str, Arg]':
        return OrderedDict((arg.name, arg) for arg in self.args)


class Include(Directive):
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
                type=Boolean,
                value=None
            )
        ]


class Skip(Directive):
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
                type=Boolean,
                value=None
            )
        ]


def get_default_directives():
    return [
        Skip(),
        Include(),
    ]
