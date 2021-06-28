from collections import deque

from hiku.denormalize.graphql import DenormalizeGraphQL


class DenormalizeEntityGraphQL(DenormalizeGraphQL):
    def __init__(self, graph, result, root_type_name):
        super().__init__(graph, result, root_type_name)
        self._type = deque([graph.__types__[root_type_name]])
