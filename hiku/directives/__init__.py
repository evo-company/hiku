from collections import OrderedDict
from dataclasses import dataclass
from typing import (
    Optional,
    List,
    Any,
)

from graphql.language import ast

from hiku.extentions import Extension
from hiku.introspection.types import (
    NON_NULL,
    SCALAR,
)


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


class DirectiveBase:
    meta: DirectiveMeta

    @property
    def name(self) -> str:
        return self.meta.name


class SchemaDirective(DirectiveBase):
    """Used to implement schema directives"""


class QueryDirective(DirectiveBase):
    """Used to implement query directives"""


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

    """
    https://spec.graphql.org/June2018/#sec--deprecated
    """
    def __init__(self, reason: Optional[str] = None):
        self.reason = reason


class Cached(QueryDirective):
    meta = DirectiveMeta(
        name='cached',
        locations=['FIELD', 'FRAGMENT_SPREAD', 'INLINE_FRAGMENT'],
        description='Caches node and all its fields',
        args=[
            DirectiveMeta.Arg(
                name='ttl',
                type_ident=NON_NULL(SCALAR('Int')),
                description='How long field will live in cache.',
                default_value=None,
            ),
        ],
    )

    def __init__(self, ttl: int):
        self.ttl = ttl


class CachedDirectiveExt(Extension):
    def on_directive_parsing(
        self, obj: ast.DirectiveNode, visitor
    ) -> Optional[QueryDirective]:
        if obj.name.value != 'cached':
            return None

        if len(obj.arguments) != 1:
            raise TypeError('@cached directive accepts exactly one '
                            'argument, {} provided'
                            .format(len(obj.arguments)))
        arg = obj.arguments[0]
        if arg.name.value != 'ttl':
            raise TypeError('@cached directive does not accept "{}" '
                            'argument'
                            .format(arg.name.value))
        ttl = visitor.visit(arg.value)  # type: ignore[attr-defined]
        if not isinstance(ttl, int):
            raise TypeError('@cached ttl argument must be an integer')

        return Cached(ttl)


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

    def __init__(self, condition: bool):
        self.condition = condition


class SkipDirectiveExt(Extension):
    def on_directive_parsing(self, obj: ast.DirectiveNode, visitor) -> Optional[QueryDirective]:
        if obj.name.value != 'skip':
            return None

        if len(obj.arguments) != 1:
            raise TypeError('@skip directive accepts exactly one '
                            'argument, {} provided'
                            .format(len(obj.arguments)))

        skip_arg = obj.arguments[0]
        if skip_arg.name.value != 'if':
            raise TypeError('@skip directive does not accept "{}" '
                            'argument'
                            .format(skip_arg.name.value))
        cond = visitor.visit(skip_arg.value)  # type: ignore[attr-defined]

        return Skip(cond)


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

    def __init__(self, condition: bool):
        self.condition = condition


class IncludeDirectiveExt(Extension):
    def on_directive_parsing(self, obj: ast.DirectiveNode, visitor) -> Optional[QueryDirective]:
        if obj.name.value != 'include':
            return None

        if len(obj.arguments) != 1:
            raise TypeError('@include directive accepts exactly one '
                            'argument, {} provided'
                            .format(len(obj.arguments)))
        arg = obj.arguments[0]
        if arg.name.value != 'if':
            raise TypeError('@include directive does not accept "{}" '
                            'argument'
                            .format(arg.name.value))
        cond = visitor.visit(arg.value)  # type: ignore[attr-defined] # noqa: E501
        return Include(cond)
