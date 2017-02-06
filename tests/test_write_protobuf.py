from __future__ import unicode_literals

from google.protobuf.message import Message

from hiku.readers.simple import read
from hiku.writers.protobuf import populate

from .protobuf import result_pb2 as t
from .test_result import GRAPH, RESULT


def msg(msg_type, data):
    msg_ = msg_type()
    for key, value in data.items():
        if isinstance(value, list):
            getattr(msg_, key).extend(value)
        elif isinstance(value, Message):
            getattr(msg_, key).CopyFrom(value)
        else:
            setattr(msg_, key, value)
    return msg_


def check_pb(query, expected):
    pb_root = t.Root()
    populate(pb_root, GRAPH, RESULT, read(query))
    assert pb_root == msg(t.Root, expected)


def test_root_fields():
    check_pb('[:slotted]', {'slotted': 'quoy_ushered'})


def test_root_fields_complex():
    check_pb('[{:tatler []}]', {})
    check_pb('[{:tatler [:orudis]}]',
             {'tatler': msg(t.Root.TatlerType, {'orudis': 'fhp_musterd'})})

    check_pb('[{:coom []}]', {})
    check_pb('[{:coom [:yappers]}]',
             {'coom': msg(t.Root.CoomType, {'yappers': 'idaho_golok'})})

    check_pb('[{:barbary []}]', {'barbary': [msg(t.Root.BarbaryType, {})]})
    check_pb('[{:barbary [:betty]}]',
             {'barbary': [msg(t.Root.BarbaryType, {'betty': 'japheth_ophir'})]})


def test_root_node_fields():
    check_pb('[{:flossy [:demoing]}]',
             {'flossy': msg(t.Root.FlossyType, {'demoing': 'judaea_bhutani'})})


def test_root_node_fields_complex():
    check_pb('[{:flossy [{:anoxic []}]}]', {})
    check_pb('[{:flossy [{:anoxic [:peeps]}]}]',
             {'flossy': msg(t.Root.FlossyType,
                            {'anoxic': msg(t.Root.FlossyType.AnoxicType,
                                           {'peeps': 'peterel_repave'})})})

    check_pb('[{:flossy [{:seggen []}]}]', {})
    check_pb('[{:flossy [{:seggen [:pensive]}]}]',
             {'flossy': msg(t.Root.FlossyType,
                            {'seggen': msg(t.Root.FlossyType.SeggenType,
                                           {'pensive': 'quebec_junkman'})})})

    check_pb('[{:flossy [{:necker []}]}]',
             {'flossy': msg(t.Root.FlossyType,
                            {'necker': [msg(t.Root.FlossyType.NeckerType,
                                            {})]})})
    check_pb('[{:flossy [{:necker [:carney]}]}]',
             {'flossy': msg(t.Root.FlossyType,
                            {'necker': [msg(t.Root.FlossyType.NeckerType,
                                            {'carney': 'calla_pedway'})]})})


def test_node_fields():
    check_pb('[{:zareeba [:nerv]} {:crowdie [:doghead]}]',
             {'zareeba': msg(t.cosies, {'nerv': 'calgary_badass'}),
              'crowdie': [msg(t.cosies, {'doghead': 'satsuma_mks'}),
                          msg(t.cosies, {'doghead': 'cached_jello'})]})


def test_node_fields_complex():
    check_pb('[{:moujik [{:went []}]}]', {})
    check_pb('[{:moujik [{:went [:changer]}]}]',
             {'moujik': msg(t.saunas,
                            {'went': msg(t.saunas.WentType,
                                         {'changer': 'cheerly_jpg'})})})

    check_pb('[{:moujik [{:atelier []}]}]', {})
    check_pb('[{:moujik [{:atelier [:litas]}]}]',
             {'moujik': msg(t.saunas,
                            {'atelier': msg(t.saunas.AtelierType,
                                            {'litas': 'facula_keck'})})})

    check_pb('[{:moujik [{:matwork []}]}]',
             {'moujik': msg(t.saunas,
                            {'matwork': [msg(t.saunas.MatworkType, {}),
                                         msg(t.saunas.MatworkType, {})]})})
    check_pb('[{:moujik [{:matwork [:bashaw]}]}]',
             {'moujik': msg(t.saunas,
                            {'matwork': [msg(t.saunas.MatworkType,
                                             {'bashaw': 'bukhoro_zins'}),
                                         msg(t.saunas.MatworkType,
                                             {'bashaw': 'worms_gemman'})]})})


def test_root_node_links():
    check_pb('[{:flossy [{:daur [:doghead]} {:peafowl [:nerv]}]}]',
             {'flossy': msg(
                 t.Root.FlossyType,
                 {'daur': msg(t.cosies, {'doghead': 'satsuma_mks'}),
                  'peafowl': [msg(t.cosies, {'nerv': 'orkneys_kumiss'}),
                              msg(t.cosies, {'nerv': 'calgary_badass'})]})})


def test_deep_links():
    check_pb(
        """
        [{:zareeba [{:mistic [:panton]} {:biopics [:tamsin]}]}
         {:crowdie [{:mistic [:tamsin]} {:biopics [:panton]}]}]
        """,
        {
            'zareeba': msg(t.cosies, {
                'mistic': msg(t.kir, {'panton': 'defina_ungot'}),
                'biopics': [msg(t.kir, {'tamsin': 'meccas_subdean'}),
                            msg(t.kir, {'tamsin': 'gimmes_oleum'})],
            }),
            'crowdie': [
                 msg(t.cosies, {
                     'mistic': msg(t.kir, {'tamsin': 'gimmes_oleum'}),
                     'biopics': [msg(t.kir, {'panton': 'defina_ungot'}),
                                 msg(t.kir, {'panton': 'jnd_toped'})]}),
                 msg(t.cosies,
                     {'mistic': msg(t.kir, {'tamsin': 'meccas_subdean'}),
                      'biopics': [msg(t.kir, {'panton': 'atajo_chow'}),
                                  msg(t.kir, {'panton': 'defina_ungot'})]})
            ]
        },
    )


def test_circle_links():
    check_pb(
        """
        [{:zareeba [{:mistic [{:bahut [:nerv]}]}]}
         {:zareeba [{:mistic [{:paramo [:nerv]}]}]}
         {:zareeba [{:biopics [{:bahut [:nerv]}]}]}
         {:zareeba [{:biopics [{:paramo [:nerv]}]}]}]
        """,
        {'zareeba': msg(t.cosies, {
            'mistic': msg(t.kir, {
                'bahut': msg(t.cosies, {'nerv': 'calgary_badass'}),
                'paramo': [
                    msg(t.cosies, {'nerv': 'orkneys_kumiss'}),
                    msg(t.cosies, {'nerv': 'deist_vined'}),
                ],
            }),
            'biopics': [
                msg(t.kir, {
                    'bahut': msg(t.cosies, {'nerv': 'orkneys_kumiss'}),
                    'paramo': [
                        msg(t.cosies, {'nerv': 'deist_vined'}),
                        msg(t.cosies, {'nerv': 'calgary_badass'}),
                    ],
                }),
                msg(t.kir, {
                    'bahut': msg(t.cosies, {'nerv': 'deist_vined'}),
                    'paramo': [
                        msg(t.cosies, {'nerv': 'calgary_badass'}),
                        msg(t.cosies, {'nerv': 'orkneys_kumiss'}),
                    ],
                }),
            ],
        })},
    )


def test_optional():
    check_pb('[{:flossy [{:daur [:doghead]} {:carf [:nerv]}]}]',
             {'flossy': msg(t.Root.FlossyType,
                            {'daur': msg(t.cosies,
                                         {'doghead': 'satsuma_mks'})})})
