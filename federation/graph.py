from hiku.graph import (
    Graph,
    Root,
    Node,
    Link,
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
        self.extend_nodes = self.get_extend_nodes(items)
        self.extend_links = self.get_extend_links(self.get_root(items).fields)
        self.extend_node_keys_map = {node.name: node.keys for node
                                     in self.extend_nodes}

        super().__init__(items, data_types)

    def get_extend_nodes(self, items):
        return [item for item in items if isinstance(item, ExtendNode)]

    def get_extend_links(self, root_fields):
        return [field for field in root_fields if isinstance(field, ExtendLink)]

    def get_root(self, items):
        # TODO no validation, be careful
        return [item for item in items if isinstance(item, Root)][0]
