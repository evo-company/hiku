from __future__ import absolute_import

from collections import defaultdict

import sqlalchemy

from ..utils import kw_only
from ..types import StringType, IntegerType
from ..graph import Field, link as _link


def _query_fields(conn, primary_key, columns_map, fields_, ids):
    if not ids:
        return []

    columns = [columns_map[field.name] for field in fields_]
    sql_expr = (
        sqlalchemy.select([primary_key] + columns)
        .where(primary_key.in_(ids))
    )
    rows = conn.execute(sql_expr).fetchall()
    rows_map = {row[primary_key]: [row[c] for c in columns]
                for row in rows}
    nulls = [None for _ in fields_]
    return [rows_map.get(id_, nulls) for id_ in ids]


def translate_type(column):
    if isinstance(column.type, sqlalchemy.Integer):
        return IntegerType
    elif isinstance(column.type, sqlalchemy.Unicode):
        return StringType
    else:
        return None


def fields(conn, table, field_names):
    """Fields maker for DB columns

    To expose `foo_table`::

        Edge(foo_table.name, fields(session, foo_table, [
            'id',
            'name',
        ]))

    """
    primary_key, = list(table.primary_key)
    columns_map = {}
    for field_name in field_names:
        try:
            column = getattr(table.c, field_name)
        except AttributeError:
            raise ValueError('Table {} does not have a column named {}'
                             .format(table, field_name))
        else:
            columns_map[field_name] = column

    def query_func(fields_, ids):
        return _query_fields(conn, primary_key, columns_map, fields_, ids)

    edge_fields = []
    for field_name in field_names:
        type_ = translate_type(getattr(table.c, field_name))
        edge_fields.append(Field(field_name, type_, query_func))
    return edge_fields


def _to_one_mapper(pairs, values):
    mapping = dict(pairs)
    return [mapping.get(value) for value in values]


def _to_many_mapper(pairs, values):
    mapping = defaultdict(list)
    for from_value, to_value in pairs:
        mapping[from_value].append(to_value)
    return [mapping[value] for value in values]


def _query_link(conn, from_column, to_column, values, mapper, proc):
    if not values:
        return []
    expr = (
        sqlalchemy.select([from_column.label('from'),
                           to_column.label('to')])
        .where(from_column.in_(values))
    )
    expr = proc(expr)
    pairs = conn.execute(expr).fetchall()
    return mapper(pairs, values)


class link(object):

    @classmethod
    def _decorator(cls, link_dec, mapper, entity, conn, **kw):
        from_column, to_column = kw_only(kw, ['from_', 'to'])
        if from_column.table is not to_column.table:
            raise ValueError('from_column and to_column should belong to '
                             'the one table')

        def decorator(proc):
            def func(ids):
                return _query_link(conn, from_column, to_column,
                                   ids, mapper, proc)
            return link_dec(entity, requires=True)(func)
        return decorator

    @classmethod
    def one(cls, entity, conn, **kw):
        return cls._decorator(_link.one, _to_one_mapper, entity, conn, **kw)

    @classmethod
    def many(cls, entity, conn, **kw):
        return cls._decorator(_link.many, _to_many_mapper, entity, conn, **kw)
