import typing as t
from .graph import Graph as Graph, Many as Many, Maybe as Maybe
from .query import Field as Field, Link as Link, Node as Node
from .types import GenericMeta as GenericMeta, OptionalMeta as OptionalMeta, RecordMeta as RecordMeta, SequenceMeta as SequenceMeta, get_type as get_type
from .utils import cached_property as cached_property
from _typeshed import Incomplete
from collections import defaultdict

class Reference:
    node: Incomplete
    ident: Incomplete
    def __init__(self, node: str, ident: t.Any) -> None: ...

ROOT: Incomplete

class Index(defaultdict):
    def __init__(self): ...
    def root(self) -> t.Dict: ...
    default_factory: Incomplete
    def finish(self) -> None: ...

class Proxy:
    __idx__: Incomplete
    __ref__: Incomplete
    __node__: Incomplete
    def __init__(self, index: Index, reference: Reference, node: Node) -> None: ...
    def __getitem__(self, item: str) -> t.Any: ...
    def __getattr__(self, name: str) -> t.Any: ...

def denormalize(graph: Graph, result: Proxy) -> t.Dict: ...
