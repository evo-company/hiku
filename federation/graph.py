from typing import (
    List,
)

from federation.service import resolve_service
from hiku.graph import (
    Graph,
    Root,
    Node,
    Field,
    Link,
)
from hiku.types import (
    Record,
    String,
    TypeRef,
)


class ExtendLink(Link):
    pass


class ExtendNode(Node):
    def __init__(self, name, fields, *, description=None, keys=None):
        """
        :param keys: primary keys for entity
            https://www.apollographql.com/docs/federation/federation-spec/#key
        """
        super().__init__(name, fields, description=description)
        self.keys = keys


class FederatedGraph(Graph):
    def __init__(self, items, data_types=None):
        extend_nodes = self.get_extend_nodes(items)

        self.extend_node_keys_map = {
            node.name: node.keys for node in extend_nodes
        }

        if not data_types:
            data_types = {}

        self.add_service_data_type(data_types)

        root = self.get_root(items)
        root = self.get_federated_root(root, items, extend_nodes)

        items = self.replace_root(items, root)

        super().__init__(items, data_types)

    def get_extend_nodes(self, items):
        return [item for item in items if isinstance(item, ExtendNode)]

    def get_extend_links(self, root_fields):
        return [field for field in root_fields if isinstance(field, ExtendLink)]

    def get_root(self, items):
        # TODO no validation, be careful
        return [item for item in items if isinstance(item, Root)][0]

    def replace_root(self, items, root):
        return [item for item in items if not isinstance(item, Root)] + [root]

    # def add_entity_data_type(self, data_types, nodes: List[ExtendNode]):
    #     type_names = [node.name for node in nodes]
    #     data_types['_Entity'] = Union[type_names]

    def add_service_data_type(self, data_types):
        data_types['_Service'] = Record[{
            'sdl': String,
        }]

    def get_federated_root(
        self,
        old_root: Root,
        items: List[Node],
        extend_nodes: List[ExtendNode],
    ) -> Root:
        extend_links = self.get_extend_links(old_root.fields)
        return Root([
            *old_root.fields,
            self.get_root_service_node(extend_links, extend_nodes),
        ])

    # TODO _service must go to federation introspection
    def get_root_service_node(self, extend_links, extend_nodes):
        return Field(
            '_service',
            TypeRef['_Service'],
            lambda fields: resolve_service(extend_links, extend_nodes),
        )
