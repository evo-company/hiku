import sys
import ast as _ast
from typing import Any

# TODO: maybe we can remove this version check
PY38: bool = sys.version_info >= (3, 8)
PY310: bool = sys.version_info >= (3, 10)


# TODO: maybe we can remove this custom class ?
class _AST:
    def __getattr__(self, name: str) -> Any:
        return getattr(_ast, name)

    arguments = _ast.arguments


ast = _AST()

if sys.version_info >= (3, 10):
    from typing import Concatenate, ParamSpec, TypeAlias
else:
    from typing_extensions import Concatenate, ParamSpec, TypeAlias

# TODO: maybe we can remove this custom class ?
if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol


__all__ = [
    "PY38",
    "PY310",
    "ast",
    "Protocol",
    "Concatenate",
    "ParamSpec",
    "TypeAlias",
]
