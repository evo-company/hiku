from contextvars import ContextVar
from typing import Iterator, Optional, Type

from prometheus_client.metrics import MetricWrapperBase

from hiku.telemetry.prometheus import (
    AsyncGraphMetrics,
    GraphMetrics,
    GraphMetricsBase,
)
from hiku.extensions.base_extension import Extension, ExtensionFactory


class _PrometheusMetricsImpl(Extension):
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

    def on_graph(self) -> Iterator[None]:
        self.execution_context.transformers = (
            self.execution_context.transformers + (self._transformer,)
        )
        yield

    def on_execute(self) -> Iterator[None]:
        if self._ctx_var is None:
            yield
        else:
            token = self._ctx_var.set(self.execution_context.context)
            yield
            self._ctx_var.reset(token)


class PrometheusMetrics(ExtensionFactory):
    ext_class = _PrometheusMetricsImpl


class _PrometheusMetricsAsyncImpl(_PrometheusMetricsImpl):
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


class PrometheusMetricsAsync(ExtensionFactory):
    ext_class = _PrometheusMetricsAsyncImpl
