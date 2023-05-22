'''
import hiku


# normal resolver
def get_name(ps: list[int], ctx: dict, opts: dict) -> 'list[str]':
    ...


# with preloader
def preload_name(ps: list[int], ctx: dict) -> list[str]:
    ...


@hiku.resolver(preload=preload_name)
def get_name(ps: list[str], ctx: dict, opts: dict) -> list[str]:
    ...


# with listify
@resolver(listify=True)
def get_company(ps: int, ctx: dict, opts: CompanyOpts) -> int | None:
    ...


# with preload and listify
@resolver(preload=preload_name, listify=True)
def get_name(ps: str, ctx: dict, opts: dict) -> str:
    ...
'''


import typing
from functools import wraps

from .option import TOptsVar
from .node import _TNode


_T = typing.TypeVar('_T')
_TO = typing.TypeVar('_TO')
_TI = typing.TypeVar('_TI')
_TContext = typing.TypeVar('_TContext', bound=dict)


_TParams = typing.ParamSpec('_TParams')


TResolver = (
    typing.Callable[[list[_TI], _TContext, TOptsVar], list[_T]]
    | typing.Callable[[list[_TI], _TContext], list[_T]]
)

TResolverListified = (
    typing.Callable[[_TI, _TContext, TOptsVar], _T]
    | typing.Callable[[_TI, _TContext], _T]
)


@typing.overload
def resolver(
    preload: typing.Callable[[list[_TI], _TContext], list[_TO]],
    listify: typing.Literal[False] = False
) -> typing.Callable[
    [TResolver[_TO, _TContext, TOptsVar, _T]],
    TResolver[_TI, _TContext, TOptsVar, _T]
]:
    ...


@typing.overload
def resolver(
    preload: typing.Callable[[list[_TI], _TContext], list[_TO]],
    listify: typing.Literal[True],
) -> typing.Callable[
    [TResolverListified[_TO, _TContext, TOptsVar, _T]],
    TResolver[_TI, _TContext, TOptsVar, _T]
]:
    ...


@typing.overload
def resolver(
    listify: typing.Literal[True],
    preload: None = None,
) -> typing.Callable[
    [TResolverListified[_TI, _TContext, TOptsVar, _T]],
    TResolver[_TI, _TContext, TOptsVar, _T]
]:
    ...


@typing.overload
def resolver(
    listify: typing.Literal[False] = False,
    preload: None = None,
) -> typing.Callable[
    [TResolver[_TI, _TContext, TOptsVar, _T]],
    TResolver[_TI, _TContext, TOptsVar, _T]
]:
    ...


def resolver(  # type: ignore
    preload: typing.Callable | None = None,
    listify: bool = False,
) -> typing.Callable:

    def decorator(
        func: typing.Callable[_TParams, _T],
    ) -> typing.Callable[_TParams, _T]:
        @wraps(func)
        def wrapper(*args: _TParams.args, **kwargs: _TParams.kwargs) -> _T:
            return func(*args, **kwargs)
        return wrapper

    return decorator


def getattr_resolve(
    preload: typing.Callable[
        [list[_TI], _TContext],
        list[typing.Any]
    ] | None = None
) -> typing.Callable[[list[_TI], _TContext, dict], list[typing.Any]]:

    @resolver(preload=preload)
    def resolve(
        keys: list[_TI],
        ctx: _TContext,
        opts: dict,
    ) -> list[typing.Any]:
        return [getattr(k, ctx['current_name']) for k in keys]

    return resolve


class require(typing.Generic[_TNode]):

    def __init__(self, *args: str):
        ...

    def __call__(self, keys: list, ctx: dict) -> list[_TNode]:
        ...
