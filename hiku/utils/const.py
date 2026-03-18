import sys
from typing import NewType, cast

Const = NewType("Const", object)


def const(name: str) -> Const:
    t = type(name, (object,), {})
    t.__module__ = sys._getframe(1).f_globals.get("__name__", "__main__")
    return cast(Const, t)
