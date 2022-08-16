from _typeshed import Incomplete
from typing import Any

PY38: bool
PY310: bool

class _AST:
    def __getattr__(self, name: str) -> Any: ...
    @staticmethod
    def arguments(_, args, vararg, kwonlyargs, kw_defaults, kwarg, defaults): ...

ast: _AST
