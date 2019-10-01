import json

import pytest

from hiku import query as hiku_query
from hiku.query import merge
from hiku.types import Record, String, Optional, Sequence, TypeRef, Integer
from hiku.graph import Graph, Link, Node, Field, Root
from hiku.result import denormalize, Index, Proxy, Reference, ROOT
from hiku.readers.simple import read


def _(*args):
    raise NotImplementedError('Data loading not implemented')


CharacterRecord = Record[{'name': String, 'stories': Sequence[String]}]
cthulhu_data = {'name': 'Cthulhu',
                'stories': ['Call of Cthulhu', 'The Dunwich Horror']}
zoth_ommog_data = {'name': 'Zoth-Ommog',
                   'stories': ['The Dweller in the Tomb', 'Out of the Ages']}

GRAPH = Graph([
    Node('cosies', [
        Field('nerv', String, _),
        Field('doghead', String, _),
        Link('mistic', TypeRef['kir'], _, requires=None),
        Link('biopics', Sequence[TypeRef['kir']], _, requires=None),
    ]),
    Node('kir', [
        Field('panton', String, _),
        Field('tamsin', String, _),
        Link('bahut', TypeRef['cosies'], _, requires=None),
        Link('paramo', Sequence[TypeRef['cosies']], _, requires=None),
    ]),
    Node('saunas', [
        Field('went', Optional[Record[{'changer': String}]], _),
        Field('atelier', Record[{'litas': String}], _),
        Field('matwork', Sequence[Record[{'bashaw': String}]], _),
    ]),
    Node('Flossy', [
        Field('demoing', String, _),
        Field('anoxic', Optional[Record[{'peeps': String}]], _),
        Field('seggen', Record[{'pensive': String}], _),
        Field('necker', Sequence[Record[{'carney': String}]], _),
        Link('daur', TypeRef['cosies'], _, requires=None),
        Link('peafowl', Sequence[TypeRef['cosies']], _, requires=None),
        Link('carf', Optional[TypeRef['cosies']], _, requires=None,)
    ]),
    Root([
        Field('slotted', String, _),
        Field('tatler', Optional[Record[{'orudis': String}]], _),
        Field('coom', Record[{'yappers': String}], _),
        Field('lovecraft', Record[{'characters': Record[{
            'cthulhu': Optional[CharacterRecord],
            'dagon': Optional[CharacterRecord],
        }]}], _),
        Field('rlyeh', Record[{'priest': CharacterRecord}], _),
        Field('elemental', Record[{
            'air': Sequence[CharacterRecord],
            'water': Sequence[CharacterRecord],
        }], _),
        Field('barbary', Sequence[Record[{'betty': String}]], _),
        Link('flossy', TypeRef['Flossy'], _, requires=None),
        Link('zareeba', TypeRef['cosies'], _, requires=None),
        Link('crowdie', Sequence[TypeRef['cosies']], _, requires=None),
        Link('moujik', TypeRef['saunas'], _, requires=None),
    ]),
])

INDEX = Index()
INDEX.root.update({
    'slotted': 'quoy_ushered',
    'tatler': {'orudis': 'fhp_musterd'},
    'coom': {'yappers': 'idaho_golok'},
    'lovecraft': {'characters': {
        'cthulhu': cthulhu_data,
        'dagon': None,
    }},
    'rlyeh': {'priest': cthulhu_data},
    'elemental': {
        'air': [],
        'water': [cthulhu_data, zoth_ommog_data],
    },
    'barbary': [{'betty': 'japheth_ophir'}],
    'flossy': Reference('Flossy', 8),
    'zareeba': Reference('cosies', 2),
    'crowdie': [Reference('cosies', 1),
                Reference('cosies', 3)],
    'moujik': Reference('saunas', 7),
})
INDEX['cosies'][1].update({
    'nerv': 'deist_vined',
    'doghead': 'satsuma_mks',
    'mistic': Reference('kir', 4),
    'biopics': [Reference('kir', 5), Reference('kir', 6)],
})
INDEX['cosies'][2].update({
    'nerv': 'calgary_badass',
    'doghead': 'kelson_popple',
    'mistic': Reference('kir', 5),
    'biopics': [Reference('kir', 6), Reference('kir', 4)],
})
INDEX['cosies'][3].update({
    'nerv': 'orkneys_kumiss',
    'doghead': 'cached_jello',
    'mistic': Reference('kir', 6),
    'biopics': [Reference('kir', 4), Reference('kir', 5)],
})
INDEX['kir'][4].update({
    'panton': 'atajo_chow',
    'tamsin': 'gimmes_oleum',
    'bahut': Reference('cosies', 1),
    'paramo': [Reference('cosies', 2), Reference('cosies', 3)],
})
INDEX['kir'][5].update({
    'panton': 'defina_ungot',
    'tamsin': 'beefs_heaters',
    'bahut': Reference('cosies', 2),
    'paramo': [Reference('cosies', 3), Reference('cosies', 1)],
})
INDEX['kir'][6].update({
    'panton': 'jnd_toped',
    'tamsin': 'meccas_subdean',
    'bahut': Reference('cosies', 3),
    'paramo': [Reference('cosies', 1), Reference('cosies', 2)],
})
INDEX['saunas'][7].update({
    'went': {'changer': 'cheerly_jpg'},
    'atelier': {'litas': 'facula_keck'},
    'matwork': [{'bashaw': 'bukhoro_zins'},
                {'bashaw': 'worms_gemman'}],
})
INDEX['Flossy'][8].update({
    'demoing': 'judaea_bhutani',
    'anoxic': {'peeps': 'peterel_repave'},
    'seggen': {'pensive': 'quebec_junkman'},
    'necker': [{'carney': 'calla_pedway'}],
    'daur': Reference('cosies', 1),
    'peafowl': [Reference('cosies', 3), Reference('cosies', 2)],
    'carf': None,
})
INDEX.finish()


def get_result(query):
    return Proxy(INDEX, ROOT, query)


def check_result(query_string, result):
    query = merge([read(query_string)])
    new_result = denormalize(GRAPH, get_result(query))
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


def test_node_fields():
    check_result('[{:zareeba [:nerv]} {:crowdie [:doghead]}]',
                 {'zareeba': {'nerv': 'calgary_badass'},
                  'crowdie': [{'doghead': 'satsuma_mks'},
                              {'doghead': 'cached_jello'}]})


def test_node_fields_complex():
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


def test_root_node_links():
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


def test_optional():
    check_result('[{:flossy [{:daur [:doghead]} {:carf [:nerv]}]}]',
                 {'flossy': {'daur': {'doghead': 'satsuma_mks'},
                             'carf': None}})


def test_nested_records():
    check_result(
        '[{:rlyeh [{:priest [:name]}]}]',
        {'rlyeh': {'priest': {'name': 'Cthulhu'}}}
    )
    check_result(
        '[{:lovecraft [{:characters [{:cthulhu [:name]}]}]}]',
        {'lovecraft': {
            'characters': {
                'cthulhu': {'name': 'Cthulhu'}
             }
        }}
    )
    check_result(
        '[{:elemental [{:air [:name]} {:water [:name :stories]}]}]',
        {'elemental': {
            'air': [],
            'water': [
                {
                    'name': 'Cthulhu',
                    'stories': ['Call of Cthulhu', 'The Dunwich Horror']
                },
                {
                    'name': 'Zoth-Ommog',
                    'stories': ['The Dweller in the Tomb',
                                'Out of the Ages']
                }
            ]
        }}
    )


def test_non_requested_field_item():
    index = Index()
    index['SomeNode'][42]['foo'] = 'bar'
    index.finish()

    ref = Reference('SomeNode', 42)
    proxy = Proxy(index, ref, hiku_query.Node([hiku_query.Field('foo')]))

    assert proxy.foo == 'bar'
    with pytest.raises(KeyError) as err:
        proxy['unknown']
    err.match(r"Field u?'unknown' wasn't requested in the query")


def test_non_requested_field_attr():
    index = Index()
    index['SomeNode'][42]['foo'] = 'bar'
    index.finish()

    ref = Reference('SomeNode', 42)
    proxy = Proxy(index, ref, hiku_query.Node([hiku_query.Field('foo')]))

    assert proxy.foo == 'bar'
    with pytest.raises(AttributeError) as err:
        proxy.unknown
    err.match(r"Field u?'unknown' wasn't requested in the query")


def test_missing_object():
    index = Index()
    index.finish()

    ref = Reference('SomeNode', 'unknown')
    proxy = Proxy(index, ref, hiku_query.Node([hiku_query.Field('foo')]))

    with pytest.raises(AssertionError) as err:
        proxy.foo
    err.match(r"Object SomeNode\[u?'unknown'\] is missing in the index")


def test_missing_field():
    index = Index()
    index['SomeNode'][42].update({})
    index.finish()

    ref = Reference('SomeNode', 42)
    proxy = Proxy(index, ref, hiku_query.Node([hiku_query.Field('foo')]))

    with pytest.raises(AssertionError) as err:
        proxy.foo
    err.match(r"Field SomeNode\[42\]\.foo is missing in the index")


def test_denormalize_with_alias():
    index = Index()
    index.root.update({
        'x': Reference('X', 'xN'),
    })
    index['X']['xN'].update({
        'a': 1,
        'b': 2,
    })
    index.finish()

    graph = Graph([
        Node('X', [
            Field('a', None, None),
            Field('b', None, None),
        ]),
        Root([
            Link('x', TypeRef['X'], lambda: 'xN', requires=None),
        ]),
    ])

    query = hiku_query.Node([
        hiku_query.Link('x', hiku_query.Node([
            hiku_query.Field('a', alias='a1'),
        ]), alias='x1'),
        hiku_query.Link('x', hiku_query.Node([
            hiku_query.Field('b', alias='b1'),
        ]), alias='x2'),
    ])

    result = Proxy(index, ROOT, query)

    assert denormalize(graph, result) == {
        'x1': {'a1': 1},
        'x2': {'b1': 2},
    }


def test_denormalize_non_merged_query():
    index = Index()
    index.root.update({
        'x': Reference('X', 'xN'),
    })
    index['X']['xN'].update({
        'a': 1,
        'b': 2,
    })
    index.finish()
    graph = Graph([
        Node('X', [
            Field('a', None, None),
            Field('b', None, None),
        ]),
        Root([
            Link('x', TypeRef['X'], lambda: 'xN', requires=None),
        ]),
    ])
    non_merged_query = hiku_query.Node([
        hiku_query.Link('x', hiku_query.Node([
            hiku_query.Field('a'),
        ])),
        hiku_query.Link('x', hiku_query.Node([
            hiku_query.Field('b'),
        ])),
    ])

    with pytest.raises(KeyError) as err:
        denormalize(graph, Proxy(index, ROOT, non_merged_query))
    err.match("Field u?'a' wasn't requested in the query")

    merged_query = merge([non_merged_query])
    assert denormalize(graph, Proxy(index, ROOT, merged_query)) == {
        'x': {'a': 1, 'b': 2},
    }


def test_denormalize_data_type():
    index = Index()
    index.root.update({'foo': {'a': 42}})
    index.finish()
    graph = Graph([
        Root([
            Field('foo', TypeRef['Foo'], None),
        ]),
    ], data_types={
        'Foo': Record[{'a': Integer}],
    })
    query = hiku_query.Node([
        hiku_query.Link('foo', hiku_query.Node([
            hiku_query.Field('a'),
        ])),
    ])
    assert denormalize(graph, Proxy(index, ROOT, query)) == {'foo': {'a': 42}}
