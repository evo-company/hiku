from __future__ import absolute_import

from . import sqlalchemy as _sa


class FieldsQuery(_sa.FieldsQuery):

    async def __call__(self, ctx, fields_, ids):
        if not ids:
            return []

        expr, result_proc = self.select_expr(fields_, ids)

        sa_engine = ctx[self.sa_engine_ctx_var]
        async with sa_engine.acquire() as connection:
            res = await connection.execute(expr)
            rows = await res.fetchall()

        return result_proc(rows)


class LinkQuery(_sa.LinkQuery):

    async def __call__(self, result_proc, ctx, ids):
        expr = self.select_expr(ids)
        if expr is None:
            pairs = []
        else:
            sa_engine = ctx[self.sa_engine_ctx_var]
            async with sa_engine.acquire() as connection:
                res = await connection.execute(expr)
                rows = await res.fetchall()
            pairs = [(r.from_column, r.to_column) for r in rows]
        return result_proc(pairs, ids)
