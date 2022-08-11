import sys
import ast as _ast
from typing import Any

PY38 = sys.version_info >= (3, 8)


class _AST:

    def __getattr__(self, name: str) -> Any:
        return getattr(_ast, name)

    if PY38:
        arguments = _ast.arguments
    else:
        @staticmethod
        def arguments(_, args, vararg, kwonlyargs, kw_defaults, kwarg, defaults):  # type: ignore[no-untyped-def] # noqa
            return _ast.arguments(args, vararg, kwonlyargs, kw_defaults, kwarg, defaults)  # noqa


ast = _AST()
