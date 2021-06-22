from unittest import TestCase

from federation.directive import KeyDirective
from federation.graph import (
    FederatedGraph,
)
from hiku.graph import (
    Root,
    Field,
    Node,
    Link,
)
from hiku.types import String, Integer, Sequence, TypeRef


def _noop():
    raise NotImplementedError


class TestFederatedGraph(TestCase):
    def test_graph_has_entities_field(self):
        GRAPH = FederatedGraph([
            Node('Astronaut', [
                Field('id', Integer, _noop),
                Field('name', String, _noop),
                Field('age', Integer, _noop),
            ], directives=[KeyDirective('id')]),
            Root([Link(
                'astronauts',
                Sequence[TypeRef['Astronaut']],
                _noop,
                requires=None,
                options=None,
            )]),
        ])
        self.assertIn('astronauts', GRAPH.root.fields_map)
        self.assertIn('_entities', GRAPH.root.fields_map)

