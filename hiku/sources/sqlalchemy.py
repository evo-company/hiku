from __future__ import absolute_import

from collections import defaultdict

import sqlalchemy

from ..utils import kw_only
from ..types import StringType, IntegerType
from ..graph import Field as FieldBase, Link as LinkBase
from ..engine import Nothing


class FieldsQuery(object):

    def __init__(self, connection, from_clause, primary_key=None):
        self.connection = connection
        self.from_clause = from_clause
        if primary_key is not None:
            self.primary_key = primary_key
        else:
            # currently only one column supported
            self.primary_key, = from_clause.primary_key

    def __call__(self, fields_, ids):
        if not ids:
            return []

        columns = [getattr(self.from_clause.c, f.name) for f in fields_]
        expr = (
            sqlalchemy.select([self.primary_key] + columns)
            .select_from(self.from_clause)
            .where(self.primary_key.in_(ids))
        )
        rows = self.connection.execute(expr).fetchall()
        rows_map = {row[self.primary_key]: [row[c] for c in columns]
                    for row in rows}

        nulls = [None for _ in fields_]
        return [rows_map.get(id_, nulls) for id_ in ids]


def _translate_type(column):
    if isinstance(column.type, sqlalchemy.Integer):
        return IntegerType
    elif isinstance(column.type, sqlalchemy.Unicode):
        return StringType
    else:
        return None


class Field(FieldBase):

    def __init__(self, name, query, **kwargs):
        try:
            column = getattr(query.from_clause.c, name)
        except AttributeError:
            raise ValueError('FromClause {} does not have a column named {}'
                             .format(query.from_clause, name))
        type_ = _translate_type(column)
        super(Field, self).__init__(name, type_, query, **kwargs)


def _to_one_mapper(pairs, values):
    mapping = dict(pairs)
    return [mapping.get(value, Nothing) for value in values]


def _to_many_mapper(pairs, values):
    mapping = defaultdict(list)
    for from_value, to_value in pairs:
        mapping[from_value].append(to_value)
    return [mapping[value] for value in values]


class LinkQuery(object):

    def __init__(self, connection, **kwargs):
        self.connection = connection
        edge, from_column, to_column, to_list = \
            kw_only(kwargs, ['edge', 'from_column', 'to_column', 'to_list'])

        if from_column.table is not to_column.table:
            raise ValueError('from_column and to_column should belong to '
                             'the one table')

        self.edge = edge
        self.from_column = from_column
        self.to_column = to_column
        self.to_list = to_list

    def __call__(self, ids):
        filtered_ids = frozenset(filter(None, ids))
        if filtered_ids:
            expr = (
                sqlalchemy.select([self.from_column.label('from_column'),
                                   self.to_column.label('to_column')])
                .where(self.from_column.in_(filtered_ids))
            )
            pairs = self.connection.execute(expr).fetchall()
        else:
            pairs = []
        mapper = _to_many_mapper if self.to_list else _to_one_mapper
        return mapper(pairs, ids)


class Link(LinkBase):

    def __init__(self, name, query, **kwargs):
        requires, options, doc = \
            kw_only(kwargs, ['requires'], ['options', 'doc'])

        super(Link, self).__init__(name, query, requires=requires,
                                   edge=query.edge, to_list=query.to_list,
                                   options=options, doc=doc)
