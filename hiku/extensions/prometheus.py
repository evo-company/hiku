from contextvars import ContextVar
from typing import Iterator, Optional, Type

from prometheus_client.metrics import MetricWrapperBase

from hiku.context import ExecutionContext
from hiku.extensions.base_extension import Extension
from hiku.telemetry.prometheus import (
    AsyncGraphMetrics,
    GraphMetrics,
    GraphMetricsBase,
)


class PrometheusMetrics(Extension):
    def __init__(
        self,
        name: str,
        *,
        metric: Optional[MetricWrapperBase] = None,
        ctx_var: Optional[ContextVar] = None,
        transformer_cls: Type[GraphMetricsBase] = GraphMetrics,
    ):
        self._name = name
        self._metric = metric
        self._ctx_var = ctx_var
        self._transformer = transformer_cls(
            self._name, metric=self._metric, ctx_var=ctx_var
        )

    def on_init(self, execution_context: ExecutionContext) -> Iterator[None]:
        execution_context.transformers = execution_context.transformers + (
            self._transformer,
        )
        yield

    def on_execute(self, execution_context: ExecutionContext) -> Iterator[None]:
        if self._ctx_var is None:
            yield
        else:
            token = self._ctx_var.set(execution_context.context)
            yield
            self._ctx_var.reset(token)


class PrometheusMetricsAsync(PrometheusMetrics):
    def __init__(
        self,
        name: str,
        *,
        metric: Optional[MetricWrapperBase] = None,
        ctx_var: Optional[ContextVar] = None,
    ):
        super().__init__(
            name,
            metric=metric,
            ctx_var=ctx_var,
            transformer_cls=AsyncGraphMetrics,
        )
