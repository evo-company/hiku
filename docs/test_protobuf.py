from hiku.graph import Graph, Node, Root, Field, Link
from hiku.types import String, Sequence, TypeRef

from basics.test_stage2 import hiku_engine, to_characters_link, character_data


GRAPH = Graph([
    Node('Character', [
        Field('name', String, character_data),
        Field('species', String, character_data),
    ]),
    Root([
        Link('characters', Sequence[TypeRef['Character']],
             to_characters_link, requires=None),
    ]),
])


def test_query_export():
    from hiku.protobuf import query_pb2

    node = query_pb2.Node()

    link = node.items.add().link
    link.name = 'characters'

    field = link.node.items.add().field
    field.name = 'name'

    from hiku.builder import build, Q
    from hiku.export.protobuf import export

    query = build([
        Q.characters[
            Q.name,
        ],
    ])

    message = export(query)
    assert message == node

    binary_message = message.SerializeToString()
    assert binary_message


def test_query_reading():
    from hiku.builder import build, Q
    from hiku.export.protobuf import export

    binary_message = export(build([Q.characters[Q.name]])).SerializeToString()

    from hiku.readers.protobuf import read

    query = read(binary_message)

    result = hiku_engine.execute_query(GRAPH, query)

    assert all(c['name'] for c in result['characters'])
