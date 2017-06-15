from __future__ import absolute_import

from abc import ABCMeta
from functools import partial
from collections import defaultdict

import sqlalchemy

from ..utils import kw_only
from ..types import String, Integer
from ..graph import Nothing, Maybe, One, Many
from ..engine import pass_context
from ..compat import with_metaclass


def _translate_type(column):
    if isinstance(column.type, sqlalchemy.Integer):
        return Integer
    elif isinstance(column.type, sqlalchemy.Unicode):
        return String
    else:
        return None


@pass_context
class FieldsQuery(object):

    def __init__(self, sa_engine_ctx_var, from_clause, **kwargs):
        primary_key, = \
            kw_only(self.__init__, kwargs, [], [('primary_key', None)])
        self.sa_engine_ctx_var = sa_engine_ctx_var
        self.from_clause = from_clause
        if primary_key is not None:
            self.primary_key = primary_key
        else:
            # currently only one column supported
            self.primary_key, = from_clause.primary_key

    def __postprocess__(self, field):
        if field.type is None:
            column = self.from_clause.c[field.name]
            field.type = _translate_type(column)

    def select_expr(self, fields_, ids):
        columns = [self.from_clause.c[f.name] for f in fields_]
        expr = (
            sqlalchemy.select([self.primary_key] + columns)
            .select_from(self.from_clause)
            .where(self.primary_key.in_(ids))
        )

        def result_proc(rows):
            rows_map = {row[self.primary_key]: [row[c] for c in columns]
                        for row in rows}

            nulls = [None for _ in fields_]
            return [rows_map.get(id_, nulls) for id_ in ids]

        return expr, result_proc

    def __call__(self, ctx, fields_, ids):
        if not ids:
            return []

        expr, result_proc = self.select_expr(fields_, ids)

        sa_engine = ctx[self.sa_engine_ctx_var]
        with sa_engine.connect() as connection:
            rows = connection.execute(expr).fetchall()

        return result_proc(rows)


def _to_maybe_mapper(pairs, values):
    mapping = dict(pairs)
    return [mapping.get(value, Nothing) for value in values]


def _to_one_mapper(pairs, values):
    mapping = dict(pairs)
    return [mapping[value] for value in values]


def _to_many_mapper(pairs, values):
    mapping = defaultdict(list)
    for from_value, to_value in pairs:
        mapping[from_value].append(to_value)
    return [mapping[value] for value in values]


class LinkQuery(with_metaclass(ABCMeta, object)):

    def __init__(self, sa_engine_ctx_var, **kwargs):
        from_column, to_column = kw_only(self.__init__, kwargs,
                                         ['from_column', 'to_column'])
        if from_column.table is not to_column.table:
            raise ValueError('from_column and to_column should belong to '
                             'one table')

        self.sa_engine_ctx_var = sa_engine_ctx_var
        self.from_column = from_column
        self.to_column = to_column

    def __postprocess__(self, link):
        if link.type_enum is One:
            func = partial(self, _to_one_mapper)
        elif link.type_enum is Maybe:
            func = partial(self, _to_maybe_mapper)
        elif link.type_enum is Many:
            func = partial(self, _to_many_mapper)
        else:
            raise TypeError(repr(link.type_enum))
        link.func = pass_context(func)

    def select_expr(self, ids):
        # TODO: make this optional, but enabled by default
        filtered_ids = frozenset(filter(None, ids))
        if filtered_ids:
            return (
                sqlalchemy.select([self.from_column.label('from_column'),
                                   self.to_column.label('to_column')])
                .where(self.from_column.in_(filtered_ids))
            )
        else:
            return None

    def __call__(self, result_proc, ctx, ids):
        expr = self.select_expr(ids)
        if expr is None:
            pairs = []
        else:
            sa_engine = ctx[self.sa_engine_ctx_var]
            with sa_engine.connect() as connection:
                pairs = connection.execute(expr).fetchall()
        return result_proc(pairs, ids)
