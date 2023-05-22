"""
# XXX: maybe dict? (TOpts = typing.TypeVar('TOpts', bound=Mapping[str, Option])
# pros:
#     explicit opts declaration at the field
# cons:
#     repetetive (type in typeddict + type in opt constructor))
#
# smth like:
#
# def option(
#     typ: type[_T],
#     nullable: bool = False,
#     default: _T | None = ...,
#     description: str | None = None,
# ) -> _T | None:
#     ...
#
# option(list[str | None], nullable=True, default=None)


import hiku
import typing


class CompanyOpts(hiku.Options):
    id: int
    aliases: list[str | None] | None = hiku.opt(
        default=None,
        description='asdf',
    )


@hiku.resolver
def get_name(ids: list[int], ctx: dict, opts: CompanyOpts) -> list[str]:

    def name_from_db(
        id1: int,
        id2: int,
        aliases: list[str | None] | None
    ) -> str:
        ...

    return [name_from_db(id_, opts.id, opts.aliases) for id_ in ids]


@hiku.node
class Product:
    field: t.ClassVar = hiku.Fieldgen[int, dict]()

    name: str = field.scalar(get_name, options=CompanyOpts)
"""

import typing
import dataclasses

_T = typing.TypeVar("_T")


@dataclasses.dataclass
class Option(typing.Generic[_T]):
    name: str
    type: type[_T]
    default: _T = ...  # type: ignore
    description: str | None = None

    def accept(self, visitor: typing.Any) -> typing.Any:
        return visitor.visit_option_decl(self)


def options(typ: type) -> type:
    ...


_Undefined = typing.NewType("_Undefined", object)


@typing.overload
def opt(
    default: type[_Undefined] = _Undefined,
    description: str | None = None,
    name: str | None = None,
) -> typing.Any:
    ...


@typing.overload
def opt(
    default: _T,
    description: str | None = None,
    name: str | None = None,
) -> _T:
    ...


def opt(
    default: typing.Any = ...,
    description: str | None = None,
    name: str | None = None,
) -> typing.Any:
    ...


# TOptsVar = typing.TypeVar('TOptsVar', bound=Options)
# TOpts = Options
TOptsVar = typing.TypeVar("TOptsVar")
TOpts = typing.Any
