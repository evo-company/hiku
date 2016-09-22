from unittest import skip

from hiku import graph as g
from hiku.expr import define, S, each, to_expr, if_some
from hiku.refs import Ref, NamedRef, ref_to_req, RequirementsExtractor
from hiku.query import Edge, Field, Link
from hiku.types import Record, Unknown, TypeRef, Sequence, Optional
from hiku.checker import check, graph_types, fn_types

from .base import reqs_eq_patcher


def _(*args, **kwargs):
    raise NotImplementedError


GRAPH = g.Graph([
    g.Edge('patens', [
        g.Field('clacks', None, _),
        g.Field('panicle', None, _),
        g.Link('apatite', TypeRef['sais'], _, requires=None),
        g.Link('jakies', Sequence[TypeRef['sais']], _, requires=None),
    ]),
    g.Edge('sais', [
        g.Field('oloroso', None, _),
        g.Field('gashes', None, _),
    ]),
    g.Root([
        g.Field('sailed', None, _),
        g.Edge('malatya', [
            g.Field('bartok', None, _),
            g.Field('rotifer', None, _),
            g.Link('teling', TypeRef['patens'], _, requires=None),
            g.Link('wandy', Sequence[TypeRef['patens']], _, requires=None),
        ]),
        g.Link('civics', Optional[TypeRef['patens']], _, requires=None),
        g.Link('weigh', TypeRef['patens'], _, requires=None),
        g.Link('comped', Sequence[TypeRef['patens']], _, requires=None),
    ]),
])


TYPES = graph_types(GRAPH)


def check_req(ref, req, add_req=None):
    with reqs_eq_patcher():
        assert ref_to_req(TYPES, ref, add_req) == req


def check_query(dsl_expr, query):
    expr, functions = to_expr(dsl_expr)
    types = TYPES.copy()
    types.update(fn_types(functions))
    expr = check(expr, types)
    expr_reqs = RequirementsExtractor.extract(types, expr)
    with reqs_eq_patcher():
        assert expr_reqs == query


def test_ref_root_field():
    check_req(NamedRef(None, 'sailed', TYPES['sailed']),
              Edge([Field('sailed')]))


def test_ref_root_edge_field():
    malatya_ref = NamedRef(None, 'malatya', TYPES['malatya'])
    check_req(malatya_ref, Edge([Link('malatya', Edge([]))]))

    bartok_ref = NamedRef(malatya_ref, 'bartok',
                          TYPES['malatya'].__field_types__['bartok'])
    check_req(bartok_ref, Edge([Link('malatya', Edge([Field('bartok')]))]))


def test_ref_link_one_edge_field():
    weigh_ref = NamedRef(None, 'weigh', TYPES['weigh'])
    check_req(weigh_ref, Edge([Link('weigh', Edge([]))]))

    patens_ref = Ref(weigh_ref, TYPES['patens'])
    check_req(patens_ref, Edge([Link('weigh', Edge([]))]))

    clacks_ref = NamedRef(patens_ref, 'clacks',
                          TYPES['patens'].__field_types__['clacks'])
    check_req(clacks_ref, Edge([Link('weigh', Edge([Field('clacks')]))]))


def test_ref_link_many_edge_field():
    comped_ref = NamedRef(None, 'comped', TYPES['comped'])
    check_req(comped_ref, Edge([Link('comped', Edge([]))]))

    patens_ref = Ref(comped_ref, TYPES['patens'])
    check_req(patens_ref, Edge([Link('comped', Edge([]))]))

    clacks_ref = NamedRef(patens_ref, 'clacks',
                          TYPES['patens'].__field_types__['clacks'])
    check_req(clacks_ref, Edge([Link('comped', Edge([Field('clacks')]))]))


def test_ref_link_maybe_edge_field():
    print(TYPES['civics'])
    civics_ref = NamedRef(None, 'civics', TYPES['civics'])
    check_req(civics_ref, Edge([Link('civics', Edge([]))]))

    patens_ref = Ref(civics_ref, TYPES['patens'])
    check_req(patens_ref, Edge([Link('civics', Edge([]))]))

    clacks_ref = NamedRef(patens_ref, 'clacks',
                          TYPES['patens'].__field_types__['clacks'])
    check_req(clacks_ref, Edge([Link('civics', Edge([Field('clacks')]))]))


def test_ref_add_req():
    check_req(NamedRef(None, 'comped', TYPES['comped']),
              Edge([Link('comped', Edge([Field('clacks'),
                                         Field('panicle')]))]),
              add_req=Edge([Field('clacks'), Field('panicle')]))


def test_query_root_field():
    check_query(S.sailed, Edge([Field('sailed')]))


def test_query_edge_field():
    check_query(
        S.weigh.clacks,
        Edge([Link('weigh', Edge([Field('clacks')]))]),
    )


def test_query_root_edge_link_field():
    check_query(
        S.malatya.teling.clacks,
        Edge([Link('malatya',
                   Edge([Link('teling', Edge([Field('clacks')]))]))]),
    )


def test_query_each_edge_field():
    check_query(
        each(S.item, S.comped, S.item.clacks),
        Edge([Link('comped', Edge([Field('clacks')]))]),
    )


def test_query_each_root_edge_link_field():
    check_query(
        each(S.item, S.malatya.wandy, S.item.clacks),
        Edge([Link('malatya', Edge([Link('wandy', Edge([Field('clacks')]))]))]),
    )


def test_query_tuple_with_edge():

    @define(Record[{'clacks': Unknown, 'panicle': Unknown}])
    def foo():
        pass

    @define(Record[{'oloroso': Unknown, 'gashes': Unknown}])
    def bar():
        pass

    sais_part = Edge([Field('oloroso'), Field('gashes')])

    # 1
    check_query(
        foo(S.weigh),
        Edge([Link('weigh', Edge([Field('clacks'), Field('panicle')]))]),
    )
    # M
    check_query(
        each(S.x, S.comped, foo(S.x)),
        Edge([Link('comped', Edge([Field('clacks'), Field('panicle')]))]),
    )
    # 1:1
    check_query(
        bar(S.weigh.apatite),
        Edge([Link('weigh', Edge([Link('apatite', Edge([Field('oloroso'),
                                                        Field('gashes')]))]))]),
    )
    # 1:M
    check_query(
        each(S.x, S.weigh.jakies, bar(S.x)),
        Edge([Link('weigh', Edge([Link('jakies', sais_part)]))]),
    )
    # M:1
    check_query(
        each(S.x, S.comped, bar(S.x.apatite)),
        Edge([Link('comped', Edge([Link('apatite', sais_part)]))]),
    )
    # M:M
    check_query(
        each(S.x, S.comped, each(S.y, S.x.jakies, bar(S.y))),
        Edge([Link('comped', Edge([Link('jakies', sais_part)]))]),
    )


def test_query_tuple_with_nested_one_edge():

    @define(Record[{'clacks': Unknown,
                    'apatite': Record[{'oloroso': Unknown,
                                       'gashes': Unknown}]}])
    def foo():
        pass

    sais_part = Edge([Field('oloroso'), Field('gashes')])

    check_query(
        foo(S.weigh),
        Edge([Link('weigh', Edge([Field('clacks'),
                                  Link('apatite', sais_part)]))]),
    )
    check_query(
        each(S.x, S.comped, foo(S.x)),
        Edge([Link('comped', Edge([Field('clacks'),
                                   Link('apatite', sais_part)]))]),
    )


@skip('fn_types() lacks information about links (one or many)')
def test_query_tuple_with_nested_many_edge():

    @define(Record[{'panicle': Unknown,
                    'jakies': Record[{'oloroso': Unknown,
                                      'gashes': Unknown}]}])
    def foo():
        pass

    sais_part = Edge([Field('oloroso'), Field('gashes')])

    check_query(
        foo(S.weigh),
        Edge([Link('weigh', Edge([Field('panicle'),
                                  Link('jakies', sais_part)]))]),
    )
    check_query(
        each(S.x, S.comped, foo(S.x)),
        Edge([Link('comped', Edge([Field('panicle'),
                                   Link('jakies', sais_part)]))]),
    )


def test_query_tuple_with_simple_args():

    @define(Record[{'clacks': Unknown, 'panicle': Unknown}],
            Unknown,
            Record[{'oloroso': Unknown, 'gashes': Unknown}],
            Unknown)
    def foo():
        pass

    check_query(
        foo(S.weigh, 1, S.weigh.apatite, 2),
        Edge([Link('weigh',
                   Edge([Field('clacks'),
                         Field('panicle'),
                         Link('apatite',
                              Edge([Field('oloroso'),
                                    Field('gashes')]))]))]),
    )


def test_query_list():

    @define(Record[{'clacks': Unknown, 'panicle': Unknown}])
    def foo():
        pass

    check_query(
        each(S.x, S.comped, [foo(S.weigh), foo(S.x)]),
        Edge([Link('comped', Edge([Field('clacks'), Field('panicle')])),
              Link('weigh', Edge([Field('clacks'), Field('panicle')]))]),
    )


def test_query_dict():

    @define(Record[{'clacks': Unknown, 'panicle': Unknown}])
    def foo():
        pass

    check_query(
        each(S.x, S.comped,
             {'a': foo(S.weigh), 'b': foo(S.x)}),
        Edge([Link('comped', Edge([Field('clacks'), Field('panicle')])),
              Link('weigh', Edge([Field('clacks'), Field('panicle')]))]),
    )


def test_query_optional():
    check_query(
        if_some([S.x, S.civics], S.x.clacks, 'false'),
        Edge([Link('civics', Edge([Field('clacks')]))]),
    )
