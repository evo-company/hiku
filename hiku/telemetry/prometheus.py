import contextvars
import time
from abc import abstractmethod
from functools import partial, update_wrapper, wraps
from typing import Dict, Optional

from prometheus_client import Summary

from ..graph import GraphTransformer
from ..engine import pass_context, _do_pass_context
from ..sources.graph import CheckedExpr


_METRIC = None


def _get_default_metric():
    global _METRIC
    if _METRIC is None:
        _METRIC = Summary(
            "graph_field_time",
            "Graph field time (seconds)",
            ["graph", "node", "field"],
        )
    return _METRIC


def _func_field_names(func):
    fields_pos = 1 if _do_pass_context(func) else 0

    @wraps(func)
    def wrapper(*args):
        return func([f.name for f in args[fields_pos]], *args)

    return wrapper


def _subquery_field_names(func):
    @wraps(func)
    def wrapper(fields, *args):
        return func([f.name for _, f in fields], fields, *args)

    return wrapper


class GraphMetricsBase(GraphTransformer):
    root_name = "Root"

    def __init__(
        self,
        name,
        *,
        metric=None,
        ctx_var: Optional[contextvars.ContextVar] = None,
    ):
        self._name = name
        self._metric = metric or _get_default_metric()
        self._ctx = ctx_var
        self._node = None
        self._wrappers: Dict = {}

    @abstractmethod
    def field_wrapper(self, observe, func):
        raise NotImplementedError

    @abstractmethod
    def link_wrapper(self, observe, func):
        raise NotImplementedError

    @abstractmethod
    def subquery_wrapper(self, observe, subquery):
        raise NotImplementedError

    def _observe_fields(self, node_name):
        by_field = {}

        def observe(start_time, field_names, ctx):
            duration = time.perf_counter() - start_time

            for name in field_names:
                try:
                    field_metric = by_field[name]
                except KeyError:
                    field_metric = by_field[name] = self._metric.labels(
                        *self.get_labels(self._name, node_name, name, ctx),
                    )
                field_metric.observe(duration)

        return observe

    def get_labels(
        self, graph_name: str, node_name: str, field_name: str, ctx: dict
    ) -> list:
        return [graph_name, node_name, field_name]

    def _wrap_field(self, node_name, func):
        observe = self._observe_fields(node_name)
        wrapper = self.field_wrapper(observe, func)
        if _do_pass_context(func):
            wrapper = pass_context(wrapper)
        wrapper = _func_field_names(wrapper)
        if _do_pass_context(func):
            wrapper = pass_context(wrapper)
        update_wrapper(wrapper, func)
        return wrapper

    def _wrap_link(self, node_name, link_name, func):
        observe = self._observe_fields(node_name)
        wrapper = self.link_wrapper(observe, func)

        if isinstance(func, partial):
            update_wrapper(wrapper, func.func, updated=())
        else:
            update_wrapper(wrapper, func)

        if _do_pass_context(func):
            wrapper = pass_context(wrapper)
        wrapper = partial(wrapper, link_name)
        if _do_pass_context(func):
            wrapper = pass_context(wrapper)
        return wrapper

    def _wrap_subquery(self, node_name, subquery):
        observe = self._observe_fields(node_name)
        wrapper = self.subquery_wrapper(observe, subquery)
        wrapper = _subquery_field_names(wrapper)
        wrapper.__subquery__ = lambda: wrapper
        return wrapper

    def visit_node(self, obj):
        self._node = obj
        try:
            return super().visit_node(obj)
        finally:
            self._node = None

    def visit_field(self, obj):
        obj = super().visit_field(obj)
        node_name = self.root_name if self._node is None else self._node.name
        if isinstance(obj.func, CheckedExpr):
            func = obj.func.__subquery__
        else:
            func = obj.func

        wrapper = self._wrappers.get(func)
        if wrapper is None:
            if isinstance(obj.func, CheckedExpr):
                wrapper = self._wrappers[func] = self._wrap_subquery(
                    node_name,
                    func,
                )
            else:
                wrapper = self._wrappers[func] = self._wrap_field(
                    node_name,
                    func,
                )

        if isinstance(obj.func, CheckedExpr):
            obj.func = CheckedExpr(
                wrapper,
                obj.func.expr,
                obj.func.reqs,
                obj.func.proc,
            )
        else:
            obj.func = wrapper
        return obj

    def visit_link(self, obj):
        obj = super().visit_link(obj)
        node_name = self.root_name if self._node is None else self._node.name
        obj.func = self._wrap_link(node_name, obj.name, obj.func)
        return obj


class _SubqueryMixin:
    def subquery_wrapper(self, observe, subquery):
        def wrapper(field_names, *args):
            start_time = time.perf_counter()
            result_proc = subquery(*args)

            def proc_wrapper():
                result = result_proc()
                ctx = self._ctx.get() if self._ctx else None
                observe(start_time, field_names, ctx)
                return result

            return proc_wrapper

        return wrapper


class GraphMetrics(_SubqueryMixin, GraphMetricsBase):
    def field_wrapper(self, observe, func):
        @wraps(func)
        def wrapper(field_names, *args):
            start_time = time.perf_counter()
            result = func(*args)
            ctx = self._ctx.get() if self._ctx else None
            observe(start_time, field_names, ctx)
            return result

        return wrapper

    def link_wrapper(self, observe, func):
        def wrapper(link_name, *args):
            start_time = time.perf_counter()
            result = func(*args)
            ctx = self._ctx.get() if self._ctx else None
            observe(start_time, [link_name], ctx)
            return result

        return wrapper


class AsyncGraphMetrics(_SubqueryMixin, GraphMetricsBase):
    def field_wrapper(self, observe, func):
        @wraps(func)
        async def wrapper(field_names, *args):
            start_time = time.perf_counter()
            result = await func(*args)
            ctx = self._ctx.get() if self._ctx else None
            observe(start_time, field_names, ctx)
            return result

        return wrapper

    def link_wrapper(self, observe, func):
        async def wrapper(link_name, *args):
            start_time = time.perf_counter()
            result = await func(*args)
            ctx = self._ctx.get() if self._ctx else None
            observe(start_time, [link_name], ctx)
            return result

        return wrapper
