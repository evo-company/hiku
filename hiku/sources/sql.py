from collections import defaultdict

from sqlalchemy import select

from ..graph import Edge, Field, Link


def _query_fields(conn, pkey, mapping, fields, ids):
    if not ids:
        return []

    ops = set([])
    columns = []
    for field in fields:
        (table, column_name), op = mapping[field.name]
        columns.append(getattr(table.c, column_name))
        if op is not None:
            ops.add(op)

    expr = select([pkey] + columns)
    for op in ops:
        expr = op(expr)

    rows = conn.execute(expr.where(pkey.in_(ids))).fetchall()
    rows_map = {row[pkey]: [row[k] for k in columns] for row in rows}
    nulls = [None for _ in fields]
    return [rows_map.get(id_, nulls) for id_ in ids]


def db_fields(conn, table, fields):
    pkey, = list(table.primary_key)
    mapping = {}

    def query_func(fields, ids):
        return _query_fields(conn, pkey, mapping, fields, ids)

    edge_fields = []
    for field in fields:
        if isinstance(field, tuple):
            sub_edge_fields = []
            sub_name, sub_table, op, sub_fields = field
            for sub_field in sub_fields:
                mapping[(sub_name, sub_field)] = ((sub_table, sub_field), op)
                sub_edge_fields.append(Field(sub_field, query_func))
            edge_fields.append(Edge(sub_name, sub_edge_fields))
        else:
            mapping[field] = ((table, field), None)
            edge_fields.append(Field(field, query_func))

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
    mapper = _to_list_mapper if to_list else _to_one_mapper

    def query_func(ids):
        return _query_link(conn, from_column, to_column, ids, mapper)

    edge = edge or to_column.table.name
    return Link(name, requires, edge, query_func, to_list=to_list)
