from typing import (
    Callable,
    Iterable,
    Any,
    List,
)

from . import sqlalchemy as _sa
from ..engine import Context
from ..query import Field

# We are limiting fetch size to reduce CPU usage and avoid event-loop blocking
FETCH_SIZE = 100


class FieldsQuery(_sa.FieldsQuery):
    async def __call__(
        self, ctx: Context, fields_: List[Field], ids: Iterable
    ) -> List:
        if not ids:
            return []

        expr, result_proc = self.select_expr(fields_, ids)

        sa_engine = ctx[self.engine_key]
        async with sa_engine.connect() as connection:
            stream = await connection.stream(expr)
            rows = []
            while True:
                bucket = await stream.fetchmany(FETCH_SIZE)
                if bucket:
                    rows.extend(bucket)
                else:
                    break

        return result_proc(rows)


class LinkQuery(_sa.LinkQuery):
    async def __call__(
        self, result_proc: Callable, ctx: Context, ids: Iterable
    ) -> Any:
        expr = self.select_expr(ids)
        if expr is None:
            pairs = []
        else:
            sa_engine = ctx[self.engine_key]
            async with sa_engine.connect() as connection:
                stream = await connection.stream(expr)
                rows = []
                while True:
                    bucket = await stream.fetchmany(FETCH_SIZE)
                    if bucket:
                        rows.extend(bucket)
                    else:
                        break
            pairs = [(r.from_column, r.to_column) for r in rows]
        return result_proc(pairs, ids)
