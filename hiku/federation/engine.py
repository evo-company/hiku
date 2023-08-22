from typing import Optional

from hiku.types import Sequence, TypeRef, Optional as HikuOptional
from hiku.cache import CacheSettings
from hiku.executors.base import SyncAsyncExecutor
from hiku.engine import Engine as _Engine
from hiku.graph import (
    GraphTransformer,
    Link,
    Many,
    Maybe,
    One,
)


def union_link_to_type(obj: Link, typ: str) -> Link:
    link = GraphTransformer().visit_link(obj)

    link.node = typ
    if link.type_enum is One:
        link.type = TypeRef[typ]
    elif link.type_enum is Maybe:
        link.type = HikuOptional[TypeRef[typ]]
    elif link.type_enum is Many:
        link.type = Sequence[TypeRef[typ]]
    else:
        raise TypeError(repr(link.type_enum))
    return link


class Engine(_Engine):
    def __init__(
        self,
        executor: SyncAsyncExecutor,
        cache: Optional[CacheSettings] = None,
    ) -> None:
        super().__init__(executor, cache)
