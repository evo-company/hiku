from unittest import skip

from hiku import graph as g
from hiku.query import Node, Field, Link
from hiku.types import Record, Unknown, TypeRef, Sequence, Optional
from hiku.expr.core import define, S, each, to_expr, if_some
from hiku.expr.refs import Ref, NamedRef, ref_to_req, RequirementsExtractor
from hiku.expr.checker import check, graph_types, fn_types

from .base import reqs_eq_patcher


def _(*args, **kwargs):
    raise NotImplementedError


GRAPH = g.Graph([
    g.Node('patens', [
        g.Field('clacks', None, _),
        g.Field('panicle', None, _),
        g.Link('una', Optional[TypeRef['sais']], _, requires=None),
        g.Link('apatite', TypeRef['sais'], _, requires=None),
        g.Link('jakies', Sequence[TypeRef['sais']], _, requires=None),
    ]),
    g.Node('sais', [
        g.Field('oloroso', None, _),
        g.Field('gashes', None, _),
    ]),
    g.Root([
        g.Field('sailed', None, _),
        g.Node('malatya', [
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
              Node([Field('sailed')]))


def test_ref_root_node_field():
    malatya_ref = NamedRef(None, 'malatya', TYPES['malatya'])
    check_req(malatya_ref, Node([Link('malatya', Node([]))]))

    bartok_ref = NamedRef(malatya_ref, 'bartok',
                          TYPES['malatya'].__field_types__['bartok'])
    check_req(bartok_ref, Node([Link('malatya', Node([Field('bartok')]))]))


def test_ref_link_one_node_field():
    weigh_ref = NamedRef(None, 'weigh', TYPES['weigh'])
    check_req(weigh_ref, Node([Link('weigh', Node([]))]))

    patens_ref = Ref(weigh_ref, TYPES['patens'])
    check_req(patens_ref, Node([Link('weigh', Node([]))]))

    clacks_ref = NamedRef(patens_ref, 'clacks',
                          TYPES['patens'].__field_types__['clacks'])
    check_req(clacks_ref, Node([Link('weigh', Node([Field('clacks')]))]))


def test_ref_link_many_node_field():
    comped_ref = NamedRef(None, 'comped', TYPES['comped'])
    check_req(comped_ref, Node([Link('comped', Node([]))]))

    patens_ref = Ref(comped_ref, TYPES['patens'])
    check_req(patens_ref, Node([Link('comped', Node([]))]))

    clacks_ref = NamedRef(patens_ref, 'clacks',
                          TYPES['patens'].__field_types__['clacks'])
    check_req(clacks_ref, Node([Link('comped', Node([Field('clacks')]))]))


def test_ref_link_maybe_node_field():
    print(TYPES['civics'])
    civics_ref = NamedRef(None, 'civics', TYPES['civics'])
    check_req(civics_ref, Node([Link('civics', Node([]))]))

    patens_ref = Ref(civics_ref, TYPES['patens'])
    check_req(patens_ref, Node([Link('civics', Node([]))]))

    clacks_ref = NamedRef(patens_ref, 'clacks',
                          TYPES['patens'].__field_types__['clacks'])
    check_req(clacks_ref, Node([Link('civics', Node([Field('clacks')]))]))


def test_ref_add_req():
    check_req(NamedRef(None, 'comped', TYPES['comped']),
              Node([Link('comped', Node([Field('clacks'),
                                         Field('panicle')]))]),
              add_req=Node([Field('clacks'), Field('panicle')]))


def test_query_root_field():
    check_query(S.sailed, Node([Field('sailed')]))


def test_query_node_field():
    check_query(
        S.weigh.clacks,
        Node([Link('weigh', Node([Field('clacks')]))]),
    )


def test_query_root_node_link_field():
    check_query(
        S.malatya.teling.clacks,
        Node([Link('malatya',
                   Node([Link('teling', Node([Field('clacks')]))]))]),
    )


def test_query_each_node_field():
    check_query(
        each(S.item, S.comped, S.item.clacks),
        Node([Link('comped', Node([Field('clacks')]))]),
    )


def test_query_each_root_node_link_field():
    check_query(
        each(S.item, S.malatya.wandy, S.item.clacks),
        Node([Link('malatya', Node([Link('wandy', Node([Field('clacks')]))]))]),
    )


def test_query_tuple_with_node():

    @define(Record[{'clacks': Unknown, 'panicle': Unknown}])
    def foo():
        pass

    @define(Record[{'oloroso': Unknown, 'gashes': Unknown}])
    def bar():
        pass

    sais_part = Node([Field('oloroso'), Field('gashes')])

    # 1
    check_query(
        foo(S.weigh),
        Node([Link('weigh', Node([Field('clacks'), Field('panicle')]))]),
    )
    # M
    check_query(
        each(S.x, S.comped, foo(S.x)),
        Node([Link('comped', Node([Field('clacks'), Field('panicle')]))]),
    )
    # 1:1
    check_query(
        bar(S.weigh.apatite),
        Node([Link('weigh', Node([Link('apatite', Node([Field('oloroso'),
                                                        Field('gashes')]))]))]),
    )
    # 1:M
    check_query(
        each(S.x, S.weigh.jakies, bar(S.x)),
        Node([Link('weigh', Node([Link('jakies', sais_part)]))]),
    )
    # M:1
    check_query(
        each(S.x, S.comped, bar(S.x.apatite)),
        Node([Link('comped', Node([Link('apatite', sais_part)]))]),
    )
    # M:M
    check_query(
        each(S.x, S.comped, each(S.y, S.x.jakies, bar(S.y))),
        Node([Link('comped', Node([Link('jakies', sais_part)]))]),
    )


def test_query_tuple_with_nested_one_node():

    @define(Record[{'clacks': Unknown,
                    'apatite': Record[{'oloroso': Unknown,
                                       'gashes': Unknown}]}])
    def foo():
        pass

    sais_part = Node([Field('oloroso'), Field('gashes')])

    check_query(
        foo(S.weigh),
        Node([Link('weigh', Node([Field('clacks'),
                                  Link('apatite', sais_part)]))]),
    )
    check_query(
        each(S.x, S.comped, foo(S.x)),
        Node([Link('comped', Node([Field('clacks'),
                                   Link('apatite', sais_part)]))]),
    )


@skip('fn_types() lacks information about links (one or many)')
def test_query_tuple_with_nested_many_node():

    @define(Record[{'panicle': Unknown,
                    'jakies': Record[{'oloroso': Unknown,
                                      'gashes': Unknown}]}])
    def foo():
        pass

    sais_part = Node([Field('oloroso'), Field('gashes')])

    check_query(
        foo(S.weigh),
        Node([Link('weigh', Node([Field('panicle'),
                                  Link('jakies', sais_part)]))]),
    )
    check_query(
        each(S.x, S.comped, foo(S.x)),
        Node([Link('comped', Node([Field('panicle'),
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
        Node([Link('weigh',
                   Node([Field('clacks'),
                         Field('panicle'),
                         Link('apatite',
                              Node([Field('oloroso'),
                                    Field('gashes')]))]))]),
    )


def test_query_list():

    @define(Record[{'clacks': Unknown, 'panicle': Unknown}])
    def foo():
        pass

    check_query(
        each(S.x, S.comped, [foo(S.weigh), foo(S.x)]),
        Node([Link('comped', Node([Field('clacks'), Field('panicle')])),
              Link('weigh', Node([Field('clacks'), Field('panicle')]))]),
    )


def test_query_dict():

    @define(Record[{'clacks': Unknown, 'panicle': Unknown}])
    def foo():
        pass

    check_query(
        each(S.x, S.comped,
             {'a': foo(S.weigh), 'b': foo(S.x)}),
        Node([Link('comped', Node([Field('clacks'), Field('panicle')])),
              Link('weigh', Node([Field('clacks'), Field('panicle')]))]),
    )


def test_query_if_some():
    check_query(
        if_some([S.x, S.civics], S.x.clacks, 'false'),
        Node([Link('civics', Node([Field('clacks')]))]),
    )


def test_query_optional_arg():

    @define(Optional[Record[{'clacks': Unknown}]])
    def foo(arg):
        pass

    check_query(
        foo(S.civics),
        Node([Link('civics', Node([Field('clacks')]))]),
    )


def test_query_nested_optional_arg():

    @define(Record[{'una': Optional[Record[{'oloroso': Unknown}]]}])
    def foo(arg):
        pass

    check_query(
        foo(S.weigh),
        Node([
            Link('weigh', Node([
                Link('una', Node([Field('oloroso')])),
            ])),
        ]),
    )
