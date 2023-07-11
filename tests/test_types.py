from hiku.types import Optional, Sequence, TypeRef


def test_sequence_to_type_ref():
    s = Sequence[TypeRef["foo"]]
    assert s.__item_type__ == TypeRef["foo"]


def test_sequence_to_optional_type_ref():
    s = Sequence[Optional[TypeRef["foo"]]]
    assert s.__item_type__ == Optional[TypeRef["foo"]]
