from ..graph import Graph as Graph
from ..query import Field as Field, Link as Link
from ..result import Proxy as Proxy
from ..types import GenericMeta as GenericMeta, OptionalMeta as OptionalMeta, SequenceMeta as SequenceMeta, TypeRefMeta as TypeRefMeta
from .base import Denormalize as Denormalize

class DenormalizeGraphQL(Denormalize):
    def __init__(self, graph: Graph, result: Proxy, root_type_name: str) -> None: ...
    def visit_field(self, obj: Field) -> None: ...
    def visit_link(self, obj: Link) -> None: ...
