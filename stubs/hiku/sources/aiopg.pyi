import sqlalchemy
from . import sqlalchemy as _sa
from ..engine import Context as Context
from ..query import Field as Field
from sqlalchemy.sql.elements import BinaryExpression as BinaryExpression
from typing import Any, Callable, Iterable, List

FETCH_SIZE: int

class FieldsQuery(_sa.FieldsQuery):
    def in_impl(self, column: sqlalchemy.Column, values: Iterable) -> BinaryExpression: ...
    async def __call__(self, ctx: Context, fields_: List[Field], ids: Iterable) -> List: ...

class LinkQuery(_sa.LinkQuery):
    def in_impl(self, column: sqlalchemy.Column, values: Iterable) -> BinaryExpression: ...
    async def __call__(self, result_proc: Callable, ctx: Context, ids: Iterable) -> Any: ...
