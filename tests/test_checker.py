from hiku.expr import S, to_expr
from hiku.refs import NamedRef
from hiku.graph import Graph, Field, Edge, Root
from hiku.types import Integer, String, Record
from hiku.checker import check, graph_types, fn_types

from .base import ref_eq_patcher, type_eq_patcher


def _(*args, **kwargs):
    raise NotImplementedError


GRAPH = Graph([
    Root([
        Field('araneus', Integer, _),
        Edge('guida', [
            Field('canette', String, _),
        ]),
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


def test_edge_field():
    expr = check_expr(S.guida.canette)
    guida_ref = NamedRef(None, 'guida', Record[{'canette': String}])
    check_ref(expr, NamedRef(guida_ref, 'canette', String))
