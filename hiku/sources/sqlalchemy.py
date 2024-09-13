from functools import partial
from collections import defaultdict
from typing import (
    Optional,
    Union,
    List,
    Any,
    Tuple,
    Callable,
    Dict,
    Iterable,
    Mapping,
)

import sqlalchemy
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.sql.expression import ColumnElement

from ..types import (
    String,
    Integer,
    IntegerMeta,
    StringMeta,
)
from ..graph import (
    Nothing,
    Maybe,
    One,
    Many,
    Link,
    Field,
)
from ..query import Field as QueryField
from ..engine import (
    pass_context,
    Context,
)

SQLALCHEMY_VERSION = tuple(map(int, sqlalchemy.__version__.split(".")))

if SQLALCHEMY_VERSION >= (1, 4):
    from sqlalchemy.engine.row import Row
else:
    from sqlalchemy.engine import RowProxy as Row


if SQLALCHEMY_VERSION >= (2, 0):

    def _process_select_params(
        params: List[ColumnElement],
    ) -> Iterable:
        return params

    def _process_result_row(row: Row) -> Mapping:
        return row._mapping

else:

    def _process_select_params(
        params: List[ColumnElement],
    ) -> Iterable:
        return (params,)

    def _process_result_row(row: Row) -> Mapping:
        return row


def _translate_type(
    column: sqlalchemy.Column,
) -> Optional[Union[IntegerMeta, StringMeta]]:
    if isinstance(column.type, sqlalchemy.Integer):
        return Integer
    elif isinstance(column.type, sqlalchemy.Unicode):
        return String
    else:
        return None


def _table_repr(table: sqlalchemy.Table) -> str:
    return "Table({})".format(
        ", ".join(
            [
                repr(table.name),
                repr(table.metadata),
                "...",
                "schema={!r}".format(table.schema),
            ]
        )
    )


@pass_context
class FieldsQuery:
    def __init__(
        self,
        engine_key: str,
        from_clause: sqlalchemy.Table,
        *,
        primary_key: Optional[sqlalchemy.Column] = None,
    ) -> None:
        self.engine_key = engine_key
        self.from_clause = from_clause
        if primary_key is not None:
            self.primary_key = primary_key
        else:
            # currently only one column supported
            (self.primary_key,) = from_clause.primary_key

    def __repr__(self) -> str:
        if isinstance(self.from_clause, sqlalchemy.Table):
            from_clause_repr = _table_repr(self.from_clause)
        else:
            from_clause_repr = repr(self.from_clause)
        return (
            "<{}.{}: engine_key={!r}, from_clause={}, primary_key={!r}>".format(
                self.__class__.__module__,
                self.__class__.__name__,
                self.engine_key,
                from_clause_repr,
                self.primary_key,
            )
        )

    def __postprocess__(self, field: Field) -> None:
        if field.type is None:
            column = self.from_clause.c[field.name]
            field.type = _translate_type(column)

    def in_impl(
        self, column: sqlalchemy.Column, values: Iterable
    ) -> BinaryExpression:
        return column.in_(values)

    def select_expr(
        self, fields_: List[QueryField], ids: Iterable
    ) -> Tuple[Select, Callable]:
        columns = [self.from_clause.c[f.name] for f in fields_]
        expr = (
            sqlalchemy.select(
                *_process_select_params([self.primary_key] + columns)
            )
            .select_from(self.from_clause)
            .where(self.in_impl(self.primary_key, ids))
        )

        def result_proc(rows: List[Row]) -> List:
            rows_map = {
                row[self.primary_key]: [row[c] for c in columns]
                for row in map(_process_result_row, rows)
            }

            nulls = [None for _ in fields_]
            return [rows_map.get(id_, nulls) for id_ in ids]

        return expr, result_proc

    def __call__(
        self, ctx: Context, fields_: List[QueryField], ids: List
    ) -> Any:
        if not ids:
            return []

        expr, result_proc = self.select_expr(fields_, ids)

        sa_engine = ctx[self.engine_key]
        with sa_engine.connect() as connection:
            rows = connection.execute(expr).fetchall()

        return result_proc(rows)


def _to_maybe_mapper(pairs: List[Tuple[Any, Any]], values: List) -> List:
    mapping: Dict = dict(pairs)
    return [mapping.get(value, Nothing) for value in values]


def _to_one_mapper(pairs: List[Tuple[Any, Any]], values: List) -> List:
    mapping = dict(pairs)
    return [mapping[value] for value in values]


def _to_many_mapper(pairs: List[Tuple], values: List) -> List:
    mapping = defaultdict(list)
    for from_value, to_value in pairs:
        mapping[from_value].append(to_value)
    return [mapping[value] for value in values]


class LinkQuery:
    def __init__(
        self,
        engine_key: str,
        *,
        from_column: sqlalchemy.Column,
        to_column: sqlalchemy.Column,
    ) -> None:
        if from_column.table is not to_column.table:
            raise ValueError(
                "from_column and to_column should belong to " "one table"
            )

        self.engine_key = engine_key
        self.from_column = from_column
        self.to_column = to_column

    def __repr__(self) -> str:
        return (
            "<{}.{}: engine_key={!r}, from_column={!r}, to_column={!r}>".format(
                self.__class__.__module__,
                self.__class__.__name__,
                self.engine_key,
                self.from_column,
                self.to_column,
            )
        )

    def __postprocess__(self, link: Link) -> None:
        if link.type_enum is One:
            func = partial(self, _to_one_mapper)
        elif link.type_enum is Maybe:
            func = partial(self, _to_maybe_mapper)
        elif link.type_enum is Many:
            func = partial(self, _to_many_mapper)
        else:
            raise TypeError(repr(link.type_enum))
        link.func = pass_context(func)

    def in_impl(
        self, column: sqlalchemy.Column, values: Iterable
    ) -> BinaryExpression:
        return column.in_(values)

    def select_expr(self, ids: Iterable) -> Optional[Select]:
        # TODO: make this optional, but enabled by default
        filtered_ids = [i for i in set(ids) if i is not None]
        if filtered_ids:
            return sqlalchemy.select(
                *_process_select_params(
                    [
                        self.from_column.label("from_column"),
                        self.to_column.label("to_column"),
                    ]
                )
            ).where(self.in_impl(self.from_column, filtered_ids))
        else:
            return None

    def __call__(
        self, result_proc: Callable, ctx: Context, ids: Iterable
    ) -> Any:
        expr = self.select_expr(ids)
        if expr is None:
            pairs = []
        else:
            sa_engine = ctx[self.engine_key]
            with sa_engine.connect() as connection:
                pairs = connection.execute(expr).fetchall()
        return result_proc(pairs, ids)
