from __future__ import unicode_literals

import json

from hiku.types import Record, String, Optional, Sequence, TypeRef
from hiku.graph import Graph, Link, Edge, Field, Root
from hiku.result import denormalize, Result
from hiku.readers.simple import read


def _():
    return 1/0


GRAPH = Graph([
    Edge('cosies', [
        Field('nerv', None, _),
        Field('doghead', None, _),
        Link('mistic', TypeRef['kir'], _, requires=None),
        Link('biopics', Sequence[TypeRef['kir']], _, requires=None),
    ]),
    Edge('kir', [
        Field('panton', None, _),
        Field('tamsin', None, _),
        Link('bahut', TypeRef['cosies'], _, requires=None),
        Link('paramo', Sequence[TypeRef['cosies']], _, requires=None),
    ]),
    Edge('saunas', [
        Field('went', Optional[Record[{'changer': String}]], _),
        Field('atelier', Record[{'litas': String}], _),
        Field('matwork', Sequence[Record[{'bashaw': String}]], _),
    ]),
    Root([
        Field('slotted', None, _),
        Field('tatler', Optional[Record[{'orudis': String}]], _),
        Field('coom', Record[{'yappers': String}], _),
        Field('barbary', Sequence[Record[{'betty': String}]], _),
        Edge('flossy', [
            Field('demoing', None, _),
            Field('anoxic', Optional[Record[{'peeps': String}]], _),
            Field('seggen', Record[{'pensive': String}], _),
            Field('necker', Sequence[Record[{'carney': String}]], _),
            Link('daur', TypeRef['cosies'], _, requires=None),
            Link('peafowl', Sequence[TypeRef['cosies']], _, requires=None),
        ]),
        Link('zareeba', TypeRef['cosies'], _, requires=None),
        Link('crowdie', Sequence[TypeRef['cosies']], _, requires=None),
        Link('moujik', TypeRef['saunas'], _, requires=None),
    ]),
])

RESULT = Result()
RESULT.root.update({
    'slotted': 'quoy_ushered',
    'tatler': {'orudis': 'fhp_musterd'},
    'coom': {'yappers': 'idaho_golok'},
    'barbary': [{'betty': 'japheth_ophir'}],
    'flossy': {
        'demoing': 'judaea_bhutani',
        'anoxic': {'peeps': 'peterel_repave'},
        'seggen': {'pensive': 'quebec_junkman'},
        'necker': [{'carney': 'calla_pedway'}],
        'daur': RESULT.ref('cosies', 1),
        'peafowl': [RESULT.ref('cosies', 3),
                    RESULT.ref('cosies', 2)],
    },
    'zareeba': RESULT.ref('cosies', 2),
    'crowdie': [RESULT.ref('cosies', 1),
                RESULT.ref('cosies', 3)],
    'moujik': RESULT.ref('saunas', 7),
})
RESULT.index.update({
    'cosies': {
        1: {
            'nerv': 'deist_vined',
            'doghead': 'satsuma_mks',
            'mistic': RESULT.ref('kir', 4),
            'biopics': [RESULT.ref('kir', 5), RESULT.ref('kir', 6)],
        },
        2: {
            'nerv': 'calgary_badass',
            'doghead': 'kelson_popple',
            'mistic': RESULT.ref('kir', 5),
            'biopics': [RESULT.ref('kir', 6), RESULT.ref('kir', 4)],
        },
        3: {
            'nerv': 'orkneys_kumiss',
            'doghead': 'cached_jello',
            'mistic': RESULT.ref('kir', 6),
            'biopics': [RESULT.ref('kir', 4), RESULT.ref('kir', 5)],
        },
    },
    'kir': {
        4: {
            'panton': 'atajo_chow',
            'tamsin': 'gimmes_oleum',
            'bahut': RESULT.ref('cosies', 1),
            'paramo': [RESULT.ref('cosies', 2), RESULT.ref('cosies', 3)],
        },
        5: {
            'panton': 'defina_ungot',
            'tamsin': 'beefs_heaters',
            'bahut': RESULT.ref('cosies', 2),
            'paramo': [RESULT.ref('cosies', 3), RESULT.ref('cosies', 1)],
        },
        6: {
            'panton': 'jnd_toped',
            'tamsin': 'meccas_subdean',
            'bahut': RESULT.ref('cosies', 3),
            'paramo': [RESULT.ref('cosies', 1), RESULT.ref('cosies', 2)],
        },
    },
    'saunas': {
        7: {
            'went': {'changer': 'cheerly_jpg'},
            'atelier': {'litas': 'facula_keck'},
            'matwork': [{'bashaw': 'bukhoro_zins'},
                        {'bashaw': 'worms_gemman'}],
        }
    },
})


def check_result(query_string, result):
    new_result = denormalize(GRAPH, RESULT, read(query_string))
    json.dumps(new_result)  # using json to check for circular references
    assert new_result == result


def test_root_fields():
    check_result('[:slotted]',
                 {'slotted': 'quoy_ushered'})


def test_root_fields_complex():
    check_result('[{:tatler []}]',
                 {'tatler': {}})
    check_result('[{:tatler [:orudis]}]',
                 {'tatler': {'orudis': 'fhp_musterd'}})

    check_result('[{:coom []}]',
                 {'coom': {}})
    check_result('[{:coom [:yappers]}]',
                 {'coom': {'yappers': 'idaho_golok'}})

    check_result('[{:barbary []}]',
                 {'barbary': [{}]})
    check_result('[{:barbary [:betty]}]',
                 {'barbary': [{'betty': 'japheth_ophir'}]})


def test_root_edge_fields():
    check_result('[{:flossy [:demoing]}]',
                 {'flossy': {'demoing': 'judaea_bhutani'}})


def test_root_edge_fields_complex():
    check_result('[{:flossy [{:anoxic []}]}]',
                 {'flossy': {'anoxic': {}}})
    check_result('[{:flossy [{:anoxic [:peeps]}]}]',
                 {'flossy': {'anoxic': {'peeps': 'peterel_repave'}}})

    check_result('[{:flossy [{:seggen []}]}]',
                 {'flossy': {'seggen': {}}})
    check_result('[{:flossy [{:seggen [:pensive]}]}]',
                 {'flossy': {'seggen': {'pensive': 'quebec_junkman'}}})

    check_result('[{:flossy [{:necker []}]}]',
                 {'flossy': {'necker': [{}]}})
    check_result('[{:flossy [{:necker [:carney]}]}]',
                 {'flossy': {'necker': [{'carney': 'calla_pedway'}]}})


def test_edge_fields():
    check_result('[{:zareeba [:nerv]} {:crowdie [:doghead]}]',
                 {'zareeba': {'nerv': 'calgary_badass'},
                  'crowdie': [{'doghead': 'satsuma_mks'},
                              {'doghead': 'cached_jello'}]})


def test_edge_fields_complex():
    check_result('[{:moujik [{:went []}]}]',
                 {'moujik': {'went': {}}})
    check_result('[{:moujik [{:went [:changer]}]}]',
                 {'moujik': {'went': {'changer': 'cheerly_jpg'}}})

    check_result('[{:moujik [{:atelier []}]}]',
                 {'moujik': {'atelier': {}}})
    check_result('[{:moujik [{:atelier [:litas]}]}]',
                 {'moujik': {'atelier': {'litas': 'facula_keck'}}})

    check_result('[{:moujik [{:matwork []}]}]',
                 {'moujik': {'matwork': [{}, {}]}})
    check_result('[{:moujik [{:matwork [:bashaw]}]}]',
                 {'moujik': {'matwork': [{'bashaw': 'bukhoro_zins'},
                                         {'bashaw': 'worms_gemman'}]}})


def test_root_edge_links():
    check_result('[{:flossy [{:daur [:doghead]} {:peafowl [:nerv]}]}]',
                 {'flossy': {'daur': {'doghead': 'satsuma_mks'},
                             'peafowl': [{'nerv': 'orkneys_kumiss'},
                                         {'nerv': 'calgary_badass'}]}})


def test_deep_links():
    check_result(
        """
        [{:zareeba [{:mistic [:panton]} {:biopics [:tamsin]}]}
         {:crowdie [{:mistic [:tamsin]} {:biopics [:panton]}]}]
        """,
        {'zareeba': {'mistic': {'panton': 'defina_ungot'},
                     'biopics': [{'tamsin': 'meccas_subdean'},
                                 {'tamsin': 'gimmes_oleum'}]},
         'crowdie': [{'mistic': {'tamsin': 'gimmes_oleum'},
                      'biopics': [{'panton': 'defina_ungot'},
                                  {'panton': 'jnd_toped'}]},
                     {'mistic': {'tamsin': 'meccas_subdean'},
                      'biopics': [{'panton': 'atajo_chow'},
                                  {'panton': 'defina_ungot'}]}]},
    )


def test_circle_links():
    check_result(
        """
        [{:zareeba [{:mistic [{:bahut [:nerv]}]}]}
         {:zareeba [{:mistic [{:paramo [:nerv]}]}]}
         {:zareeba [{:biopics [{:bahut [:nerv]}]}]}
         {:zareeba [{:biopics [{:paramo [:nerv]}]}]}]
        """,
        {'zareeba': {  # cosies 2
            'mistic': {  # kir 5
                'bahut': {'nerv': 'calgary_badass'},  # cosies 2
                'paramo': [
                    {'nerv': 'orkneys_kumiss'},  # cosies 3
                    {'nerv': 'deist_vined'},  # cosies 1
                ],
            },
            'biopics': [
                {  # kir 6
                    'bahut': {'nerv': 'orkneys_kumiss'},  # cosies 3
                    'paramo': [
                        {'nerv': 'deist_vined'},  # cosies 1
                        {'nerv': 'calgary_badass'},  # cosies 2
                    ],
                },
                {  # kir 4
                    'bahut': {'nerv': 'deist_vined'},  # cosies 1
                    'paramo': [
                        {'nerv': 'calgary_badass'},  # cosies 2
                        {'nerv': 'orkneys_kumiss'},  # cosies 3
                    ],
                },
            ],
        }},
    )
