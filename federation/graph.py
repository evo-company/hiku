from typing import (
    List,
    Optional,
    Dict,
)

from hiku.graph import (
    Graph,
    Node,
    Field,
    Option,
)
from hiku.types import (
    Record,
    Sequence,
    Union,
    Any,
)


class FederatedGraph(Graph):
    def __init__(
            self,
            items: List[Node],
            data_types: Optional[Dict[str, 'Record']] = None,
    ):
        for item in items:
            if item.name is None:
                item.fields.append(
                    Field('_entities', Sequence[Union['_Entity']], lambda: None,
                          options=[
                              Option('representations', Sequence[Any['_Any']])
                          ])
                )

        super().__init__(items, data_types)
