from typing import (
    Callable,
    Iterable,
    Any,
    List,
    Iterator,
    Tuple,
)

import sqlalchemy
from sqlalchemy.sql import Select
from sqlalchemy import any_
from sqlalchemy.sql.elements import BinaryExpression

from . import sqlalchemy as _sa
from ..engine import Context
from ..query import Field

# We are limiting fetch size to reduce CPU usage and avoid event-loop blocking
FETCH_SIZE = 100


def _uniq_fields(fields: List[Field]) -> Iterator[Field]:
    visited = set()
    for f in fields:
        if f.name not in visited:
            visited.add(f.name)
            yield f


class FieldsQuery(_sa.FieldsQuery):
    def in_impl(
        self, column: sqlalchemy.Column, values: Iterable
    ) -> BinaryExpression:
        return column == any_(values)

    def select_expr(
        self, fields_: List[Field], ids: Iterable
    ) -> Tuple[Select, Callable]:
        result_columns = [self.from_clause.c[f.name] for f in fields_]
        # aiopg requires unique columns to be passed to select,
        # otherwise it will raise an error
        query_columns = [
            column
            for f in _uniq_fields(fields_)
            if (column := self.from_clause.c[f.name]) != self.primary_key
        ]

        expr = (
            sqlalchemy.select(
                *_sa._process_select_params([self.primary_key] + query_columns)
            )
            .select_from(self.from_clause)
            .where(self.in_impl(self.primary_key, ids))
        )

        def result_proc(rows: List[_sa.Row]) -> List:
            rows_map = {
                row[self.primary_key]: [row[c] for c in result_columns]
                for row in map(_sa._process_result_row, rows)
            }

            nulls = [None for _ in fields_]
            return [rows_map.get(id_, nulls) for id_ in ids]

        return expr, result_proc

    async def __call__(
        self, ctx: Context, fields_: List[Field], ids: Iterable
    ) -> List:
        if not ids:
            return []

        expr, result_proc = self.select_expr(fields_, ids)

        sa_engine = ctx[self.engine_key]
        async with sa_engine.acquire() as connection:
            res = await connection.execute(expr)
            rows = []
            while True:
                bucket = await res.fetchmany(FETCH_SIZE)
                if bucket:
                    rows.extend(bucket)
                else:
                    break

        return result_proc(rows)


class LinkQuery(_sa.LinkQuery):
    def in_impl(
        self, column: sqlalchemy.Column, values: Iterable
    ) -> BinaryExpression:
        return column == any_(values)

    async def __call__(
        self, result_proc: Callable, ctx: Context, ids: Iterable
    ) -> Any:
        expr = self.select_expr(ids)
        if expr is None:
            pairs = []
        else:
            sa_engine = ctx[self.engine_key]
            async with sa_engine.acquire() as connection:
                res = await connection.execute(expr)
                rows = []
                while True:
                    bucket = await res.fetchmany(FETCH_SIZE)
                    if bucket:
                        rows.extend(bucket)
                    else:
                        break
            pairs = [(r.from_column, r.to_column) for r in rows]
        return result_proc(pairs, ids)
