import typing

import pytest

import hiku.types
from hiku.classes.node import node
from hiku.classes.types import _LazyTypeRef, lazy, raw_type, ref, to_hiku_type

if typing.TYPE_CHECKING:
    from tests.classes.droid import Droid


@pytest.mark.parametrize(
    "typ,expected",
    [
        # basic scalars
        (int, raw_type(hiku.types.Integer)),
        (float, raw_type(hiku.types.Float)),
        (str, raw_type(hiku.types.String)),
        (bool, raw_type(hiku.types.Boolean)),
        # scalars in containers, old + new types
        (list[int], raw_type(hiku.types.Sequence[hiku.types.Integer])),
        (list[float], raw_type(hiku.types.Sequence[hiku.types.Float])),
        (list[str], raw_type(hiku.types.Sequence[hiku.types.String])),
        (list[bool], raw_type(hiku.types.Sequence[hiku.types.Boolean])),
        (int | None, raw_type(hiku.types.Optional[hiku.types.Integer])),
        (float | None, raw_type(hiku.types.Optional[hiku.types.Float])),
        (str | None, raw_type(hiku.types.Optional[hiku.types.String])),
        (bool | None, raw_type(hiku.types.Optional[hiku.types.Boolean])),
        (typing.List[int], raw_type(hiku.types.Sequence[hiku.types.Integer])),
        (typing.List[float], raw_type(hiku.types.Sequence[hiku.types.Float])),
        (typing.List[str], raw_type(hiku.types.Sequence[hiku.types.String])),
        (typing.List[bool], raw_type(hiku.types.Sequence[hiku.types.Boolean])),
        (
            typing.Optional[int],
            raw_type(hiku.types.Optional[hiku.types.Integer]),
        ),
        (
            typing.Optional[float],
            raw_type(hiku.types.Optional[hiku.types.Float]),
        ),
        (
            typing.Optional[str],
            raw_type(hiku.types.Optional[hiku.types.String]),
        ),
        (
            typing.Optional[bool],
            raw_type(hiku.types.Optional[hiku.types.Boolean]),
        ),
        # some complex cases
        (
            list[int | None],
            raw_type(
                hiku.types.Sequence[hiku.types.Optional[hiku.types.Integer]]
            ),
        ),
        (
            typing.List[typing.Optional[int]],
            raw_type(
                hiku.types.Sequence[hiku.types.Optional[hiku.types.Integer]]
            ),
        ),
        (
            list[str] | None,
            raw_type(
                hiku.types.Optional[hiku.types.Sequence[hiku.types.String]]
            ),
        ),
        (
            typing.Optional[typing.List[str]],
            raw_type(
                hiku.types.Optional[hiku.types.Sequence[hiku.types.String]]
            ),
        ),
        # some absurd stuff just for the sake of it
        (
            list[list[bool | None]] | None,
            raw_type(
                hiku.types.Optional[
                    hiku.types.Sequence[
                        hiku.types.Sequence[
                            hiku.types.Optional[hiku.types.Boolean]
                        ]
                    ]
                ]
            ),
        ),
        (
            typing.Optional[typing.List[typing.List[typing.Optional[bool]]]],
            raw_type(
                hiku.types.Optional[
                    hiku.types.Sequence[
                        hiku.types.Sequence[
                            hiku.types.Optional[hiku.types.Boolean]
                        ]
                    ]
                ]
            ),
        ),
    ],
)
def test_to_hiku_type__scalars(typ, expected):
    assert to_hiku_type(typ) == expected


@pytest.mark.parametrize(
    "typ",
    [
        complex,
        tuple,
        typing.Any,
        None,
        1,
        list,
        typing.Optional,
        int | str,
        typing.Union[bool, float],
        typing.Annotated[int, lazy(".")],
        ref["Droid"],
    ],
)
def test_to_hiku_type__raises(typ):
    with pytest.raises(ValueError):
        to_hiku_type(typ)


@node(name="HumanNodeName")
class Human:
    __key__: int

    id: int


@pytest.mark.parametrize(
    "typ,expected",
    [
        (ref[Human], raw_type(hiku.types.TypeRef["HumanNodeName"])),
        (
            ref[Human] | None,
            raw_type(hiku.types.Optional[hiku.types.TypeRef["HumanNodeName"]]),
        ),
        (
            typing.Optional[ref[Human]],
            raw_type(hiku.types.Optional[hiku.types.TypeRef["HumanNodeName"]]),
        ),
        (
            list[ref[Human]],
            raw_type(hiku.types.Sequence[hiku.types.TypeRef["HumanNodeName"]]),
        ),
        (
            typing.List[ref[Human]],
            raw_type(hiku.types.Sequence[hiku.types.TypeRef["HumanNodeName"]]),
        ),
    ],
)
def test_to_hiku_type__ref(typ, expected):
    assert to_hiku_type(typ) == expected


@pytest.mark.parametrize(
    "typ,expected",
    [
        (
            typing.Annotated[ref["Droid"], lazy(".droid")],
            _LazyTypeRef(
                classname="Droid",
                module=".droid",
                package="tests.classes",
            ),
        ),
        (
            typing.Annotated[ref["Droid"], lazy("tests.classes.droid")],
            _LazyTypeRef(
                classname="Droid",
                module="tests.classes.droid",
                package=None,
            ),
        ),
        (
            typing.Annotated[ref["Droid"] | None, lazy("tests.classes.droid")],
            _LazyTypeRef(
                classname="Droid",
                module="tests.classes.droid",
                package=None,
                containers=[hiku.types.Optional],
            ),
        ),
        (
            typing.Optional[
                typing.Annotated[ref["Droid"], lazy("tests.classes.droid")]
            ],
            _LazyTypeRef(
                classname="Droid",
                module="tests.classes.droid",
                package=None,
                containers=[hiku.types.Optional],
            ),
        ),
        (
            typing.Annotated[list[ref["Droid"]], lazy("tests.classes.droid")],
            _LazyTypeRef(
                classname="Droid",
                module="tests.classes.droid",
                package=None,
                containers=[hiku.types.Sequence],
            ),
        ),
        (
            typing.Annotated[
                typing.List[ref["Droid"]], lazy("tests.classes.droid")
            ],
            _LazyTypeRef(
                classname="Droid",
                module="tests.classes.droid",
                package=None,
                containers=[hiku.types.Sequence],
            ),
        ),
        (
            typing.Annotated[
                list[list[ref["Droid"] | None]] | None,
                lazy("tests.classes.droid"),
            ],
            _LazyTypeRef(
                classname="Droid",
                module="tests.classes.droid",
                package=None,
                containers=[
                    hiku.types.Optional,
                    hiku.types.Sequence,
                    hiku.types.Sequence,
                    hiku.types.Optional,
                ],
            ),
        ),
    ],
)
def test_to_hiku_type__lazy_ref(typ, expected):
    assert to_hiku_type(typ) == expected


@pytest.mark.parametrize(
    "typ,expected",
    [
        (
            typing.Annotated[typing.Any, raw_type(hiku.types.Any)],
            raw_type(hiku.types.Any),
        ),
        (
            typing.Annotated[str, raw_type(hiku.types.ID)],
            raw_type(hiku.types.ID),
        ),
        (
            typing.Annotated[
                list[float | None] | None,
                raw_type(
                    hiku.types.Optional[
                        hiku.types.Sequence[
                            hiku.types.Optional[hiku.types.Float]
                        ]
                    ]
                ),
            ],
            raw_type(
                hiku.types.Optional[
                    hiku.types.Sequence[hiku.types.Optional[hiku.types.Float]]
                ]
            ),
        ),
        (
            typing.Annotated[None, raw_type(hiku.types.TypeRef["SomeNode"])],
            raw_type(hiku.types.TypeRef["SomeNode"]),
        ),
        (
            typing.Annotated[None, raw_type(hiku.types.UnionRef["SomeUnion"])],
            raw_type(hiku.types.UnionRef["SomeUnion"]),
        ),
        (
            typing.Annotated[
                None, raw_type(hiku.types.InterfaceRef["SomeIface"])
            ],
            raw_type(hiku.types.InterfaceRef["SomeIface"]),
        ),
        (
            typing.Annotated[None, raw_type(hiku.types.EnumRef["SomeEnum"])],
            raw_type(hiku.types.EnumRef["SomeEnum"]),
        ),
    ],
)
def test_to_hiku_type__raw_type(typ, expected):
    assert to_hiku_type(typ) == expected
