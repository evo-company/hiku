import hashlib
from typing import Iterator

from sentry_sdk import configure_scope, start_span

from hiku.context import ExecutionContext
from hiku.extensions.base_extension import Extension


class SentryTracing(Extension):
    def get_resource_name(self, execution_context: ExecutionContext) -> str:
        assert execution_context.query

        query_hash = self._hash_query(execution_context.query_src)

        if execution_context.operation_name:
            return f"{execution_context.operation_name}:{query_hash}"

        return query_hash

    def _hash_query(self, query: str) -> str:
        return hashlib.md5(query.encode("utf-8")).hexdigest()

    def on_operation(
        self, execution_context: ExecutionContext
    ) -> Iterator[None]:
        self._operation_name = execution_context.operation_name
        name = self._operation_name or "Anonymous Query"

        with configure_scope() as scope:
            if scope.span:
                self.gql_span = scope.span.start_child(
                    op="gql", description=name
                )
            else:
                self.gql_span = start_span(op="gql")

        operation_type = execution_context.operation_type_name

        self.gql_span.set_tag("graphql.operation_type", operation_type)
        self.gql_span.set_tag(
            "graphql.resource_name", self.get_resource_name(execution_context)
        )
        self.gql_span.set_data("graphql.query", execution_context.query_src)

        yield

        self.gql_span.finish()

    def on_validate(
        self, execution_context: ExecutionContext
    ) -> Iterator[None]:
        self.validation_span = self.gql_span.start_child(
            op="validation", description="Validation"
        )

        yield

        self.validation_span.finish()

    def on_parse(self, execution_context: ExecutionContext) -> Iterator[None]:
        self.parsing_span = self.gql_span.start_child(
            op="parsing", description="Parsing"
        )

        yield

        self.parsing_span.finish()
