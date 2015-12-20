from sqlalchemy import select

from hiku.graph import Edge, Field


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
    return [rows_map.get(id_) for id_ in ids]
