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
    (String, FieldTypeInfo('String', FieldType.SCALAR, required=True)),
    (Integer, FieldTypeInfo('Integer', FieldType.SCALAR, required=True)),
    (Float, FieldTypeInfo('Float', FieldType.SCALAR, required=True)),
    (ID, FieldTypeInfo('ID', FieldType.SCALAR, required=True)),
    (Any, FieldTypeInfo('Any', FieldType.SCALAR, required=True)),
    (Mapping, FieldTypeInfo('Mapping', FieldType.SCALAR, required=True)),
    (Optional[String], FieldTypeInfo('String', FieldType.SCALAR, required=False)),
    (Sequence[String], FieldTypeInfo('String', FieldType.SCALAR, required=True)),

    # None
    (None, None),
    (Optional, None),
    (Sequence, None),

    # records
    (TypeRef['UserRecord'], FieldTypeInfo('UserRecord', FieldType.RECORD, required=True)),
    (Optional[TypeRef['UserRecord']], FieldTypeInfo('UserRecord', FieldType.RECORD, required=False)),
    (Sequence[TypeRef['UserRecord']], FieldTypeInfo('UserRecord', FieldType.RECORD, required=True)),

    # enums
    (EnumRef['UserRecord'], FieldTypeInfo('UserRecord', FieldType.ENUM, required=True)),
    (Optional[EnumRef['UserRecord']], FieldTypeInfo('UserRecord', FieldType.ENUM, required=False)),
    (Sequence[EnumRef['UserRecord']], FieldTypeInfo('UserRecord', FieldType.ENUM, required=True)),

    # custom scalars
    (DateTime, FieldTypeInfo('DateTime', FieldType.CUSTOM_SCALAR, required=True)),
    (Optional[DateTime], FieldTypeInfo('DateTime', FieldType.CUSTOM_SCALAR, required=False)),
    (Sequence[DateTime], FieldTypeInfo('DateTime', FieldType.CUSTOM_SCALAR, required=True)),
])
def test_field_type(field_type, type_info):
    info = get_field_info(field_type)
    assert info == type_info
