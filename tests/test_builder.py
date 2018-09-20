from hiku.query import Node, Field, Link
from hiku.builder import build, Q


def test():
    query = build([
        Q.aliased_tyan << Q.tyan,
        Q.aliased_turlock << Q.turlock[
            Q.gange
        ],
        Q.tiber(ramsons='defaces')[
            Q.decifer(botches='auxerre'),
            Q.exocet(brogues='hygiea'),
        ],
    ])
    assert query == Node([
        Field('tyan', alias='aliased_tyan'),
        Link('turlock', Node([Field('gange')]), alias='aliased_turlock'),
        Link('tiber', Node([
            Field('decifer', options={'botches': 'auxerre'}),
            Field('exocet', options={'brogues': 'hygiea'}),
        ]), {'ramsons': 'defaces'}),
    ])
