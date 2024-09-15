import sys

PY310: bool = sys.version_info >= (3, 10)


if sys.version_info >= (3, 10):
    from typing import Concatenate, ParamSpec, TypeAlias
else:
    from typing_extensions import Concatenate, ParamSpec, TypeAlias


__all__ = [
    "PY310",
    "Concatenate",
    "ParamSpec",
    "TypeAlias",
]
