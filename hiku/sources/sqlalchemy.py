from __future__ import absolute_import

from collections import defaultdict

import sqlalchemy
from sqlalchemy import select

from ..types import StringType, IntegerType
from ..graph import Field, Link


def _query_fields(conn, primary_key, columns_map, fields, ids):
    if not ids:
        return []

    columns = [columns_map[field.name] for field in fields]
    sql_expr = select([primary_key] + columns).where(primary_key.in_(ids))
    rows = conn.execute(sql_expr).fetchall()
    rows_map = {row[primary_key]: [row[c] for c in columns]
                for row in rows}
    nulls = [None for _ in fields]
    return [rows_map.get(id_, nulls) for id_ in ids]


def translate_type(column):
    if isinstance(column.type, sqlalchemy.Integer):
        return IntegerType
    elif isinstance(column.type, sqlalchemy.Unicode):
        return StringType
    else:
        return None


def db_fields(conn, table, fields):
    """Fields maker for DB columns

    To expose `foo_table`::

        Edge(foo_table.name, db_fields(session, foo_table, [
            'id',
            'name',
        ]))

    """
    primary_key, = list(table.primary_key)
    columns_map = {}
    for field_name in fields:
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
    for field_name in fields:
        type_ = translate_type(getattr(table.c, field_name))
        edge_fields.append(Field(field_name, type_, query_func))
    return edge_fields


def _to_one_mapper(pairs, values):
    mapping = dict(pairs)
    return [mapping.get(value) for value in values]


def _to_list_mapper(pairs, values):
    mapping = defaultdict(list)
    for from_value, to_value in pairs:
        mapping[from_value].append(to_value)
    return [mapping[value] for value in values]


def _query_link(conn, from_column, to_column, values, mapper):
    if not values:
        return []
    pairs = (
        conn.execute(select([from_column, to_column])
                     .where(from_column.in_(values)))
        .fetchall()
    )
    return mapper(pairs, values)


def db_link(conn, name, requires, from_column, to_column, to_list,
            edge=None):
    """Link maker for DB relations

    OneToOne with backward reference::

        # From foo to bar, where bar.c.foo_id references single foo.c.id
        db_link(conn, 'bar', requires='id', from_column=bar.c.foo_id,
                to_column=bar.c.id, to_list=False)

    ManyToOne and OneToOne with forward reference::

        # No query required, we have direct link
        Link('bar_link', 'bar_id', 'bar', lambda ids: ids, to_list=False)

    OneToMany::

        # From foo to bar, where bar.c.foo_id references many foo.c.id
        db_link(conn, 'bars', requires='id', from_column=bar.c.foo_id,
                to_column=bar.c.id, to_list=True)

    ManyToMany::

        # From foo to bar via f2b, with f2b.foo_id and f2b.bar_id references
        db_link(conn, 'bars', requires='id', from_column=f2b.c.foo_id,
                to_column=f2b.c.bar_id, to_list=True)

    """
    if from_column.table is not to_column.table:
        raise ValueError('from_column and to_column should belong to '
                         'the one table')

    mapper = _to_list_mapper if to_list else _to_one_mapper

    def query_func(ids):
        return _query_link(conn, from_column, to_column, ids, mapper)

    edge = edge or to_column.table.name
    return Link(name, requires, edge, query_func, to_list=to_list)
