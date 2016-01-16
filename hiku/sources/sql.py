from collections import defaultdict

from sqlalchemy import select

from ..graph import Edge, Field, Link


def db_fields(conn, table, fields):
    pkey, = list(table.primary_key)
    mapping = {}

    def query_func(fields, ids):
        return query_fields(conn, pkey, mapping, fields, ids)

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


def db_link(conn, name, from_, to_, to_list):
    if not to_list:
        def query_func(ids):
            return ids
    else:
        def query_func(ids):
            return query_link_o2m(conn, to_, ids)

    return Link(name, from_.name, to_.table.name, query_func, to_list)


def query_fields(conn, pkey, mapping, fields, ids):
    if not ids:
        return []

    ops = set([])
    columns = []
    for field in fields:
        (table, column_name), op = mapping[field]
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


def query_link_o2m(conn, to_, ids):
    to_pkey, = list(to_.table.primary_key)
    rows = (
        conn.execute(select([to_pkey, to_])
                     .where(to_.in_(ids)))
        .fetchall()
    )
    mapping = defaultdict(list)
    for pkey, ref in rows:
        mapping[pkey].append(ref)
    return [mapping[id_] for id_ in ids]
