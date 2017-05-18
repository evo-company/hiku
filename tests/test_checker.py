import pytest

from hiku.graph import Graph, Field, Node, Root, Link
from hiku.types import Integer, String, Record, Optional, TypeRef
from hiku.expr.core import S, to_expr, if_some, define
from hiku.expr.refs import NamedRef, Ref
from hiku.expr.nodes import List, Symbol
from hiku.expr.checker import check, graph_types, fn_types

from .base import ref_eq_patcher, type_eq_patcher


def _(*args, **kwargs):
    raise NotImplementedError


GRAPH = Graph([
    Node('thalweg', [
        Field('pinout', Integer, _),
    ]),
    Root([
        Field('araneus', Integer, _),
        Field('peen', Optional[Record[{'copies': Integer}]], _),
        Node('guida', [
            Field('canette', String, _),
        ]),
        Link('rakyats', Optional[TypeRef['thalweg']], _, requires=None),
    ]),
])

TYPES = graph_types(GRAPH)


def check_expr(expr):
    expr, functions = to_expr(expr)
    types = TYPES.copy()
    types.update(fn_types(functions))
    return check(expr, types)


def check_ref(node, ref):
    with ref_eq_patcher(), type_eq_patcher():
        assert node.__ref__ == ref


def test_root_field():
    expr = check_expr(S.araneus)
    check_ref(expr, NamedRef(None, 'araneus', TYPES['araneus']))


def test_node_field():
    expr = check_expr(S.guida.canette)
    guida_ref = NamedRef(None, 'guida', Record[{'canette': String}])
    check_ref(expr, NamedRef(guida_ref, 'canette', String))


def test_optional_field():
    expr = check_expr(if_some([S.x, S.peen], S.x.copies, 0))
    if_some_bind = expr.values[1]
    assert isinstance(if_some_bind, List)
    x = if_some_bind.values[0]
    assert isinstance(x, Symbol)
    peen_ref = NamedRef(None, 'peen', Optional[Record[{'copies': Integer}]])
    check_ref(x, Ref(peen_ref, Record[{'copies': Integer}]))


def test_optional_link():
    expr = check_expr(if_some([S.x, S.rakyats], S.x.pinout, ''))
    if_some_bind = expr.values[1]
    assert isinstance(if_some_bind, List)
    x = if_some_bind.values[0]
    assert isinstance(x, Symbol)
    rakyats_ref = NamedRef(None, 'rakyats', Optional[TypeRef['thalweg']])
    check_ref(x, Ref(rakyats_ref, TypeRef['thalweg']))


def test_optional_arg():

    @define(Optional[Record[{'pinout': Integer}]])
    def foo():
        pass

    @define(Optional[Record[{'invalid': Integer}]])
    def bar():
        pass

    check_expr(foo(S.rakyats))

    with pytest.raises(TypeError) as err:
        check_expr(bar(S.rakyats))

    assert err.match('Missing field invalid')
