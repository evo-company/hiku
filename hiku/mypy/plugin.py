from typing import Type as TypingType

from mypy.errorcodes import ErrorCode
from mypy.nodes import (
    IndexExpr,
    Context,
    StrExpr,
)
from mypy.plugin import (
    FunctionContext,
    Plugin,
    CheckerPluginInterface,
)
from mypy.types import Type


ERROR_GRAPH_LINK_INVALID_OPTIONAL_TYPE = ErrorCode('hiku-graph-link', 'Invalid Link Optional type', 'Hiku')
ERROR_GRAPH_LINK_INVALID_TYPE_REF_REF = ErrorCode('hiku-graph-link', 'Invalid Link TypeRef ref', 'Hiku')


def error_invalid_optional_link_type(api: CheckerPluginInterface, context: Context) -> None:
    api.fail('Link second argument Optional accepts only TypeRef in this context. Hint: Optional[TypeRef])', context, code=ERROR_GRAPH_LINK_INVALID_OPTIONAL_TYPE)


def error_invalid_optional_link_type_ref_ref(api: CheckerPluginInterface, context: Context) -> None:
    api.fail('Link second argument Optional[TypeRef[<>]] must reference existing Node in graph. Hint: Optional[TypeRef["node_name"]])', context, code=ERROR_GRAPH_LINK_INVALID_TYPE_REF_REF)


def _hiku_graph_link_hook(ctx: FunctionContext) -> Type:
    if ctx.api.path != 'examples/graphql_federation.py':
        return ctx.default_return_type

    assert ctx.callee_arg_names[1] == 'type_'
    type_arg = ctx.args[1]
    if isinstance(type_arg[0], IndexExpr):
        index_expr = type_arg[0]
        if index_expr.base.fullname == 'hiku.types.Optional':
            # base is NameExpr
            if index_expr.index.base.fullname != 'hiku.types.TypeRef':
                error_invalid_optional_link_type(ctx.api, ctx.context)
                return ctx.default_return_type

            if not isinstance(index_expr.index.index, StrExpr):
                error_invalid_optional_link_type_ref_ref(ctx.api, ctx.context)
                return ctx.default_return_type

    return ctx.default_return_type


class HikuPlugin(Plugin):
    def get_function_hook(self, fullname: str):
        if fullname == 'hiku.graph.Link':
            return _hiku_graph_link_hook


def plugin(version: str) -> TypingType[Plugin]:
    """Plugin entrypoint"""
    return HikuPlugin
