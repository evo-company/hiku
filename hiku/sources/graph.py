from functools import partial
from typing import (
    NoReturn,
    List,
    Tuple,
    Union,
    Callable,
    Iterator,
    cast,
)

from .. import query
from ..compat import TypeAlias
from ..executors.queue import (
    Queue,
    TaskSet,
)
from ..expr.nodes import Node
from ..graph import (
    Link,
    Nothing,
    Graph,
    Field,
)
from ..types import TypeRef, Sequence
from ..query import (
    merge,
    Node as QueryNode,
    Field as QueryField,
    Link as QueryLink,
)
from ..types import Any
from ..engine import (
    Query,
    Context,
)
from ..expr.refs import RequirementsExtractor
from ..expr.core import (
    to_expr,
    S,
    THIS,
    DotHandler,
    _Func,
)
from ..expr.checker import check, fn_types
from ..expr.compiler import ExpressionCompiler


FieldGroup = Tuple[Field, Union[QueryField, QueryLink]]
Expr: TypeAlias = Union[_Func, DotHandler]


def _create_result_proc(
    engine_query: Query, procs: List[Callable], options: List
) -> Callable[[], List[List]]:
    def result_proc() -> List[List]:
        sq_result = engine_query.result()
        return [
            [
                proc(this, sq_result, *opt_args)
                for proc, opt_args in zip(procs, options)
            ]
            for this in sq_result[THIS]
        ]

    return result_proc


def _yield_options(
    query_field: QueryField, graph_field: Field
) -> Iterator[Any]:
    options = query_field.options or {}
    for option in graph_field.options:
        value = options.get(option.name, option.default)
        if value is Nothing:
            raise TypeError(
                'Required option "{}" for {!r} was not provided'.format(
                    option.name, graph_field
                )
            )
        else:
            yield value


class BoundExpr:
    def __init__(self, sub_graph: "SubGraph", expr: Expr) -> None:
        self.sub_graph = sub_graph
        self.expr = expr

    def __repr__(self) -> str:
        expr, _ = to_expr(self.expr)
        return "<{}: sub_graph={!r}, expr={!r}>".format(
            self.__class__.__name__, self.sub_graph, expr
        )

    def __postprocess__(self, field: Field) -> None:
        expr, funcs = to_expr(self.expr)

        env = fn_types(funcs)
        env.update(self.sub_graph.types["__root__"].__field_types__)
        env.update((opt.name, opt.type or Any) for opt in field.options)
        env[THIS] = TypeRef[self.sub_graph.node]

        expr = check(expr, self.sub_graph.types, env)

        option_names_set = set(opt.name for opt in field.options)
        reqs = RequirementsExtractor.extract(self.sub_graph.types, expr)
        reqs = query.Node(
            [f for f in reqs.fields if f.name not in option_names_set]
        )

        option_names = [opt.name for opt in field.options]
        code = ExpressionCompiler.compile_lambda_expr(expr, option_names)
        proc = partial(
            eval(compile(code, "<expr>", "eval")),
            {f.__def_name__: f.__def_body__ for f in funcs},  # type: ignore[attr-defined] # noqa: E501
        )
        field.func = CheckedExpr(self.sub_graph, expr, reqs, proc)  # type: ignore[assignment] # noqa: E501

    def __call__(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise TypeError("Expression is not checked: {!r}".format(self.expr))


class CheckedExpr:
    def __init__(
        self, sub_graph: "SubGraph", expr: Node, reqs: QueryNode, proc: Callable
    ) -> None:
        self.sub_graph = sub_graph
        self.expr = expr
        self.reqs = reqs
        self.proc = proc

    def __repr__(self) -> str:
        return "<{}: sub_graph={!r}, expr={!r}, reqs={!r}>".format(
            self.__class__.__name__, self.sub_graph, self.expr, self.reqs
        )

    @property
    def __subquery__(self) -> "SubGraph":
        return self.sub_graph


class SubGraph:
    def __init__(self, graph: Graph, node: str) -> None:
        self.graph = graph
        self.node = node
        self.types = graph.__types__

    def __repr__(self) -> str:
        return "<{}: node={!r}>".format(self.__class__.__name__, self.node)

    @property
    def __subquery__(self) -> "SubGraph":
        return self

    def __postprocess__(self, field: Field) -> None:
        BoundExpr(self, getattr(S.this, field.name)).__postprocess__(field)

    def __call__(
        self,
        fields: List[FieldGroup],
        ids: List,
        queue: Queue,
        ctx: Context,
        task_set: TaskSet,
    ) -> Callable[[], List[List]]:
        path = tuple(["this"])
        this_graph_link = Link(THIS, Sequence[TypeRef[self.node]], None, requires=None)  # type: ignore # noqa: E501

        reqs = merge([gf.func.reqs for gf, _ in fields])  # type: ignore[union-attr]  # noqa: E501
        procs = [gf.func.proc for gf, _ in fields]  # type: ignore[union-attr]
        option_values = []
        for gf, qf in fields:
            if gf.options and qf.options:
                option_values.append(
                    [qf.options[opt.name] for opt in gf.options]
                )
            else:
                option_values.append([])

        this_query_link = cast(query.Link, reqs.fields_map[THIS])
        other_reqs = query.Node([r for r in reqs.fields if r.name != THIS])

        q = Query(queue, task_set, self.graph, reqs, ctx)
        q.process_link(
            path,
            self.graph.root,
            this_graph_link,
            this_query_link,
            None,
            ids,
        )
        q.process_node(path, self.graph.root, other_reqs, None)
        return _create_result_proc(q, procs, option_values)

    def compile(self, expr: Expr) -> BoundExpr:
        return BoundExpr(self, expr)

    def c(self, expr: Expr) -> BoundExpr:
        return self.compile(expr)
