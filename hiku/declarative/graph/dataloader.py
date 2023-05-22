"""Dataloaders as a replacement for db graph, more in __init__.py """

import typing
import collections.abc


_T = typing.TypeVar("_T")


class Dataloader(typing.Generic[_T]):
    def load(
        self, *args
    ) -> collections.abc.Callable[[list[_T], dict], list["typing.Self"]]:
        ...

    def __call__(self, keys: list, ctx: dict) -> list["typing.Self"]:
        ...
