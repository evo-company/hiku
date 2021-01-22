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


class Arg(NamedTuple):
    description: str
    type: Any


class Directive(ABC):
    @property
    @abstractmethod
    def name(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def locations(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def args(self) -> Dict[str, Arg]:
        """Directive arguments"""
        pass

    def value_info(self, fields):
        info = {'name': self.name,
                'description': self.description,
                'locations': self.locations}
        yield [info[f.name] for f in fields]


class IncludeDirective(Directive):
    @property
    def name(self) -> str:
        return 'include'

    @property
    def locations(self) -> List[str]:
        return ['FIELD', 'FRAGMENT_SPREAD', 'INLINE_FRAGMENT']

    @property
    def description(self) -> str:
        return (
            'Directs the executor to include this field or fragment '
            'only when the `if` argument is true.'
        )

    @property
    def args(self) -> Dict[str, Arg]:
        return {
            'if': Arg(
                description='Included when true.',
                type=NON_NULL(SCALAR('Boolean'))
            )
        }


class SkipDirective(Directive):
    @property
    def name(self) -> str:
        return 'skip'

    @property
    def locations(self) -> List[str]:
        return ['FIELD', 'FRAGMENT_SPREAD', 'INLINE_FRAGMENT']

    @property
    def description(self) -> str:
        return (
            'Directs the executor to skip this field or fragment '
            'when the `if` argument is true.'
        )

    @property
    def args(self) -> Dict[str, Arg]:
        return {
            'if': Arg(
                description='Skipped when true.',
                type=NON_NULL(SCALAR('Boolean'))
            )
        }


directive_registry = {
    'skip': SkipDirective(),
    'include': IncludeDirective(),
}
