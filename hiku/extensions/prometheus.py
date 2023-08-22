from typing import Iterator, Optional, Type

from prometheus_client.metrics import MetricWrapperBase

from hiku.telemetry.prometheus import (
    AsyncGraphMetrics,
    GraphMetrics,
    GraphMetricsBase,
    metrics_ctx,
)
from hiku.extensions.base_extension import Extension


class PrometheusMetrics(Extension):
    def __init__(
        self,
        name: str,
        metric: Optional[MetricWrapperBase] = None,
        transformer_cls: Type[GraphMetricsBase] = GraphMetrics,
    ):
        self._name = name
        self._metric = metric
        self._transformer = transformer_cls(self._name, metric=self._metric)

    def on_graph(self) -> Iterator[None]:
        self.execution_context.transformers = (
            self.execution_context.transformers + (self._transformer,)
        )
        yield

    def on_execute(self) -> Iterator[None]:
        token = metrics_ctx.set(self.execution_context.context)
        yield
        metrics_ctx.reset(token)


class PrometheusMetricsAsync(PrometheusMetrics):
    def __init__(
        self,
        name: str,
        metric: Optional[MetricWrapperBase] = None,
    ):
        super().__init__(name, metric=metric, transformer_cls=AsyncGraphMetrics)
