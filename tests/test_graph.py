import pytest

from hiku.graph import Field, FieldType, FieldTypeInfo, Graph, Link, Node, Root, get_field_info
from hiku.scalar import DateTime
from hiku.types import Any, EnumRef, Float, ID, Integer, Mapping, Optional, Sequence, String, TypeRef


def noop(*args, **kwargs):
    pass


def test_link_with_sequence_to_type_ref():
    graph = Graph([
        Node('A', [
            Field('a', String, noop)
        ]),
        Root([
            Link('a', Sequence[TypeRef['A']], noop, requires=None)
        ])
    ])

    assert len(graph.nodes) == 1


def test_link_with_sequence_to_optional_type_ref():
    graph = Graph([
        Node('A', [
            Field('a', String, noop)
        ]),
        Root([
            Link('a', Sequence[Optional[TypeRef['A']]], noop, requires=None)
        ])
    ])

    assert len(graph.nodes) == 1


@pytest.mark.parametrize("field_type, type_info", [
    # scalars
    (String, FieldTypeInfo('String', FieldType.SCALAR)),
    (Integer, FieldTypeInfo('Integer', FieldType.SCALAR)),
    (Float, FieldTypeInfo('Float', FieldType.SCALAR)),
    (ID, FieldTypeInfo('ID', FieldType.SCALAR)),
    (Any, FieldTypeInfo('Any', FieldType.SCALAR)),
    (Mapping, FieldTypeInfo('Mapping', FieldType.SCALAR)),
    (Optional[String], FieldTypeInfo('String', FieldType.SCALAR)),
    (Sequence[String], FieldTypeInfo('String', FieldType.SCALAR)),

    # None
    (None, None),
    (Optional, None),
    (Sequence, None),

    # records
    (TypeRef['UserRecord'], FieldTypeInfo('UserRecord', FieldType.RECORD)),
    (Optional[TypeRef['UserRecord']], FieldTypeInfo('UserRecord', FieldType.RECORD)),
    (Sequence[TypeRef['UserRecord']], FieldTypeInfo('UserRecord', FieldType.RECORD)),

    # enums
    (EnumRef['UserRecord'], FieldTypeInfo('UserRecord', FieldType.ENUM)),
    (Optional[EnumRef['UserRecord']], FieldTypeInfo('UserRecord', FieldType.ENUM)),
    (Sequence[EnumRef['UserRecord']], FieldTypeInfo('UserRecord', FieldType.ENUM)),

    # custom scalars
    (DateTime, FieldTypeInfo('DateTime', FieldType.CUSTOM_SCALAR)),
    (Optional[DateTime], FieldTypeInfo('DateTime', FieldType.CUSTOM_SCALAR)),
    (Sequence[DateTime], FieldTypeInfo('DateTime', FieldType.CUSTOM_SCALAR)),
])
def test_field_type(field_type, type_info):
    info = get_field_info(field_type)
    assert info == type_info
