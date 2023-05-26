from typing import Any, Callable


class cached_property:
    def __init__(self, func: Callable) -> None:
        self.__doc__ = getattr(func, "__doc__")
        self.func = func

    def __get__(self, obj: Any, cls: Any) -> Any:
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value
