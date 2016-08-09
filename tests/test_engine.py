from __future__ import unicode_literals

from concurrent.futures import ThreadPoolExecutor

from hiku import query
from hiku.graph import Graph, Edge, Field, Link, Option, Root, Many
from hiku.types import Record, Sequence, Integer, Optional
from hiku.engine import Engine
from hiku.readers.simple import read
from hiku.executors.threads import ThreadsExecutor

from .base import patch, reqs_eq_patcher, check_result


def query_fields1(*args, **kwargs):
    pass


def query_fields2(*args, **kwargs):
    pass


def query_fields3(*args, **kwargs):
    pass


def query_link1(*args, **kwargs):
    pass


def query_link2(*args, **kwargs):
    pass


def _(func):
    def wrapper(*args, **kwargs):
        return globals()[func.__name__](*args, **kwargs)
    return wrapper


def _patch(func):
    return patch('{}.{}'.format(__name__, getattr(func, '__name__')))


GRAPH = Graph([
    Edge('tergate', [
        # simple fields
        Field('arion', _(query_fields1)),
        Field('bhaga', _(query_fields2)),
        # complex fields
        Field('eches', Optional[Record[{'gone': Integer}]],
              _(query_fields1)),
        Field('lappin', Record[{'sodden': Integer}],
              _(query_fields2)),
        Field('ant', Sequence[Record[{'circlet': Integer}]],
              _(query_fields3)),
    ]),
    Root([
        Field('indice', _(query_fields1)),
        Field('unmined', _(query_fields2)),
        Edge('kameron', [
            Field('buran', _(query_fields1)),
            Field('updated', _(query_fields2)),
        ]),
        Link('subaru', Many, _(query_link1), edge='tergate', requires=None),
        Link('jessie', Many, _(query_link2), edge='tergate', requires=None),
        # with options
        Link('doubled', Many, _(query_link1), edge='tergate', requires=None,
             options=[Option('empower', default="deedily_reaving")]),
    ]),
])

thread_pool = ThreadPoolExecutor(2)


def execute(query_):
    engine = Engine(ThreadsExecutor(thread_pool))
    return engine.execute(GRAPH, read(query_))


def test_root_fields():
    with _patch(query_fields1) as qf1, _patch(query_fields2) as qf2:
        qf1.return_value = ['boiardo_sansei']
        qf2.return_value = ['isolde_bust_up']
        check_result(execute('[:indice :unmined]'),
                     {'indice': 'boiardo_sansei',
                      'unmined': 'isolde_bust_up'})
        with reqs_eq_patcher():
            qf1.assert_called_once_with([query.Field('indice')])
            qf2.assert_called_once_with([query.Field('unmined')])


def test_root_edge_fields():
    with _patch(query_fields1) as qf1, _patch(query_fields2) as qf2:
        qf1.return_value = ['khios_iid']
        qf2.return_value = ['cambay_cricket']
        check_result(execute('[{:kameron [:buran :updated]}]'),
                     {'kameron': {'buran': 'khios_iid',
                                  'updated': 'cambay_cricket'}})
        with reqs_eq_patcher():
            qf1.assert_called_once_with([query.Field('buran')])
            qf2.assert_called_once_with([query.Field('updated')])


def test_edge_fields():
    with \
            _patch(query_fields1) as qf1,\
            _patch(query_fields2) as qf2,\
            _patch(query_link1) as ql1:

        ql1.return_value = [1]
        qf1.return_value = [['harkis_sanest']]
        qf2.return_value = [['slits_smiddy']]
        result = execute('[{:subaru [:arion :bhaga]}]')
        check_result(result,
                     {'subaru': [{'arion': 'harkis_sanest',
                                  'bhaga': 'slits_smiddy'}]})
        assert result.index == {'tergate': {1: {'arion': 'harkis_sanest',
                                                'bhaga': 'slits_smiddy'}}}
        with reqs_eq_patcher():
            ql1.assert_called_once_with()
            qf1.assert_called_once_with([query.Field('arion')], [1])
            qf2.assert_called_once_with([query.Field('bhaga')], [1])


def test_edge_complex_fields():
    with \
            _patch(query_link1) as ql1,\
            _patch(query_fields1) as qf1,\
            _patch(query_fields2) as qf2,\
            _patch(query_fields3) as qf3:

        ql1.return_value = [1]
        qf1.return_value = [[{'gone': 'marshes_welted'}]]
        qf2.return_value = [[{'sodden': 'colline_inlined'}]]
        qf3.return_value = [[[{'circlet': 'magi_syght'}]]]

        check_result(
            execute(
                '[{:subaru [{:eches [:gone]} '
                '           {:lappin [:sodden]} '
                '           {:ant [:circlet]}]}]'
            ),
            {'subaru': [{'eches': {'gone': 'marshes_welted'},
                         'lappin': {'sodden': 'colline_inlined'},
                         'ant': [{'circlet': 'magi_syght'}]}]},
        )

        with reqs_eq_patcher():
            ql1.assert_called_once_with()
            qf1.assert_called_once_with([
                query.Link('eches',
                           query.Edge([query.Field('gone')]))],
                [1],
            )
            qf2.assert_called_once_with([
                query.Link('lappin',
                           query.Edge([query.Field('sodden')]))],
                [1],
            )
            qf3.assert_called_once_with([
                query.Link('ant',
                           query.Edge([query.Field('circlet')]))],
                [1],
            )


def test_links():
    with \
            _patch(query_fields1) as qf1,\
            _patch(query_fields2) as qf2,\
            _patch(query_link1) as ql1,\
            _patch(query_link2) as ql2:

        ql1.return_value = [1]
        qf1.return_value = [['boners_friezes']]
        ql2.return_value = [2]
        qf2.return_value = [['julio_mousy']]
        result = execute('[{:subaru [:arion]} {:jessie [:bhaga]}]')
        check_result(result, {'subaru': [{'arion': 'boners_friezes'}],
                              'jessie': [{'bhaga': 'julio_mousy'}]})
        assert result.index == {'tergate': {1: {'arion': 'boners_friezes'},
                                            2: {'bhaga': 'julio_mousy'}}}
        with reqs_eq_patcher():
            ql1.assert_called_once_with()
            qf1.assert_called_once_with([query.Field('arion')], [1])
            ql2.assert_called_once_with()
            qf2.assert_called_once_with([query.Field('bhaga')], [2])


def test_field_options():
    with _patch(query_fields1) as qf1:
        qf1.return_value = ['baking_murse']
        result = execute('[(:indice {:staithe "maria_bubkus"})]')
        check_result(result, {'indice': 'baking_murse'})
        with reqs_eq_patcher():
            qf1.assert_called_once_with([
                query.Field('indice', options={'staithe': 'maria_bubkus'}),
            ])


def test_link_option():
    with _patch(query_link1) as ql1, _patch(query_fields1) as qf1:
        ql1.return_value = [1]
        qf1.return_value = [['aunder_hagg']]
        result = execute('[{(:doubled {:empower "heaven_duncery"}) [:arion]}]')
        check_result(result, {'doubled': [{'arion': 'aunder_hagg'}]})
        with reqs_eq_patcher():
            ql1.assert_called_once_with({'empower': 'heaven_duncery'})
            qf1.assert_called_once_with([query.Field('arion')], [1])


def test_link_option_default():
    with _patch(query_link1) as ql1, _patch(query_fields1) as qf1:
        ql1.return_value = [1]
        qf1.return_value = [['lend_rounded']]
        result = execute('[{:doubled [:arion]}]')
        check_result(result, {'doubled': [{'arion': 'lend_rounded'}]})
        with reqs_eq_patcher():
            ql1.assert_called_once_with({'empower': 'deedily_reaving'})
            qf1.assert_called_once_with([query.Field('arion')], [1])


def test_link_option_unknown():
    with _patch(query_link1) as ql1, _patch(query_fields1) as qf1:
        ql1.return_value = [1]
        qf1.return_value = [['tarweed_tolled']]
        result = execute('[{(:doubled {:empower "hanna_gourds" '
                         '             :varying "dread_linty"}) '
                         '  [:arion]}]')
        check_result(result, {'doubled': [{'arion': 'tarweed_tolled'}]})
        with reqs_eq_patcher():
            ql1.assert_called_once_with({'empower': 'hanna_gourds'})
            qf1.assert_called_once_with([query.Field('arion')], [1])
