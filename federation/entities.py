from abc import (
    abstractmethod,
    ABC,
)
from typing import (
    List,
    Any,
)

from hiku.graph import (
    Field,
)


class FederatedResolver(ABC):
    @abstractmethod
    def resolve_references(
        self,
        refs: List[dict],
        fields: List[Field]
    ) -> List[Any]:
        pass


def resolve_entities(entities_link, items):
    items_map = {item.name: item for item in items}

    _entity_fields = entities_link.node.fields
    representations = entities_link.options.get('representations')

    entity_type = representations[0]['__typename']
    if entity_type not in items_map:
        raise TypeError(f'Type {entity_type} not defined in graph')

    entity_node = items_map[entity_type]
    resolver: FederatedResolver = entity_node.fields[0].func

    result = resolver.resolve_references(representations, _entity_fields)

    return [result]
