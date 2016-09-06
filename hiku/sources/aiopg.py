from __future__ import absolute_import

import asyncio

from hiku.sources import sqlalchemy as _sa


class FieldsQuery(_sa.FieldsQuery):

    @asyncio.coroutine
    def __call__(self, ctx, fields_, ids):
        if not ids:
            return []

        expr, result_proc = self.__select_expr__(fields_, ids)

        sa_engine = ctx[self.sa_engine_ctx_var]
        with (yield from sa_engine) as connection:
            res = yield from connection.execute(expr)
            rows = yield from res.fetchall()

        return result_proc(rows)


Field = _sa.Field


class LinkQuery(_sa.LinkQuery):

    @asyncio.coroutine
    def __call__(self, ctx, ids):
        expr, result_proc = self.__select_expr__(ids)
        if expr is None:
            pairs = []
        else:
            sa_engine = ctx[self.sa_engine_ctx_var]
            with (yield from sa_engine) as connection:
                res = yield from connection.execute(expr)
                rows = yield from res.fetchall()
            pairs = [(r.from_column, r.to_column) for r in rows]
        return result_proc(pairs)


Link = _sa.Link
