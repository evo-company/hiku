from typing import (
    Optional,
    Union,
    TYPE_CHECKING,
    Any,
)

<<<<<<< Updated upstream
if TYPE_CHECKING:
    from hiku.graph import Field, Link
=======
from graphql.language import ast

from hiku.introspection.types import (
    NON_NULL,
    SCALAR,
)


def get_directive(
    name: str,
    directives: List[ast.DirectiveNode]
) -> Optional[ast.DirectiveNode]:
    return next((d for d in directives if d.name.value == name), None)


@dataclass(frozen=True)
class DirectiveMeta:
    @dataclass(frozen=True)
    class Arg:
        name: str
        type_ident: Any
        description: str
        default_value: Any

    name: str
    locations: List[str]
    description: str
    args: List[Arg]

    @property
    def args_map(self) -> OrderedDict:
        return OrderedDict((arg.name, arg) for arg in self.args)
>>>>>>> Stashed changes


class DirectiveBase:
    pass


<<<<<<< Updated upstream
class Deprecated(DirectiveBase):
=======
class QueryDirective(DirectiveBase):
    """Used to implement query directives"""
    # TODO: if directive has options (args) then must pass as second argument ?
    # TODO: or it will be available via self ? like self.ttl ?
    # TODO: async execute ?
    def execute(self, value: Any) -> Any:
        return value


class Deprecated(SchemaDirective):
    meta = DirectiveMeta(
        name='deprecated',
        locations=['FIELD_DEFINITION', 'ENUM_VALUE'],
        description='Marks the field or enum value as deprecated',
        args=[
            DirectiveMeta.Arg(
                name='reason',
                type_ident=SCALAR('String'),
                description='Deprecation reason.',
                default_value=None,
            ),
        ],
    )

>>>>>>> Stashed changes
    """
    https://spec.graphql.org/June2018/#sec--deprecated
    """
    def __init__(self, reason: Optional[str] = None):
        self.reason = reason

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_deprecated_directive(self)


<<<<<<< Updated upstream
def get_deprecated(field: Union['Field', 'Link']) -> Optional[Deprecated]:
    """Get deprecated directive"""
    return next(
        (d for d in field.directives if isinstance(d, Deprecated)),
        None
    )


class QueryDirective:
    def __init__(self, name: str) -> None:
        self.name = name


class Cached(QueryDirective):
    def __init__(self, ttl: int):
        super().__init__('cached')
        self.ttl = ttl
=======

class Skip(QueryDirective):
    meta = DirectiveMeta(
        name='skip',
        locations=['FIELD', 'FRAGMENT_SPREAD', 'INLINE_FRAGMENT'],
        description=(
            'Directs the executor to skip this field or fragment '
            'when the `if` argument is true.'
        ),
        args=[
            DirectiveMeta.Arg(
                name='if',
                type_ident=NON_NULL(SCALAR('Boolean')),
                description='Skipped when true.',
                default_value=None,
            ),
        ],
    )


class Include(QueryDirective):
    meta = DirectiveMeta(
        name='include',
        locations=['FIELD', 'FRAGMENT_SPREAD', 'INLINE_FRAGMENT'],
        description=(
            'Directs the executor to include this field or fragment '
            'only when the `if` argument is true.'
        ),
        args=[
            DirectiveMeta.Arg(
                name='if',
                type_ident=NON_NULL(SCALAR('Boolean')),
                description='Included when true.',
                default_value=None,
            ),
        ],
    )
>>>>>>> Stashed changes
