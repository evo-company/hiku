from __future__ import unicode_literals

import json

from hiku.graph import Graph, Link, Edge, Field, Root, Many, One
from hiku.result import denormalize, Result
from hiku.readers.simple import read


def _():
    return 1/0


GRAPH = Graph([
    Edge('cosies', [
        Field('nerv', _),
        Field('doghead', _),
        Link('mistic', One, _, edge='kir', requires=None),
        Link('biopics', Many, _, edge='kir', requires=None),
    ]),
    Edge('kir', [
        Field('panton', _),
        Field('tamsin', _),
        Link('bahut', One, _, edge='cosies', requires=None),
        Link('paramo', Many, _, edge='cosies', requires=None),
    ]),
    Root([
        Field('slotted', _),
        Edge('flossy', [
            Field('demoing', _),
            Link('daur', One, _, edge='cosies', requires=None),
            Link('peafowl', Many, _, edge='cosies', requires=None),
        ]),
        Link('zareeba', One, _, edge='cosies', requires=None),
        Link('crowdie', Many, _, edge='cosies', requires=None),
    ]),
])

RESULT = Result()
RESULT.update({
    'slotted': 'quoy_ushered',
    'flossy': {
        'demoing': 'judaea_bhutani',
        'daur': RESULT.ref('cosies', 1),
        'peafowl': [RESULT.ref('cosies', 3),
                    RESULT.ref('cosies', 2)],
    },
    'zareeba': RESULT.ref('cosies', 2),
    'crowdie': [RESULT.ref('cosies', 1),
                RESULT.ref('cosies', 3)],
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
    }
})


def check_result(query_string, result):
    new_result = denormalize(GRAPH, RESULT, read(query_string))
    json.dumps(new_result)  # using json to check for circular references
    assert new_result == result


def test_root_fields():
    check_result('[:slotted]',
                 {'slotted': 'quoy_ushered'})


def test_root_fields_complex():
    pass  # TODO


def test_root_edge_fields():
    check_result('[{:flossy [:demoing]}]',
                 {'flossy': {'demoing': 'judaea_bhutani'}})


def test_root_edge_fields_complex():
    pass  # TODO


def test_edge_fields():
    check_result('[{:zareeba [:nerv]} {:crowdie [:doghead]}]',
                 {'zareeba': {'nerv': 'calgary_badass'},
                  'crowdie': [{'doghead': 'satsuma_mks'},
                              {'doghead': 'cached_jello'}]})


def test_edge_fields_complex():
    pass  # TODO


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
