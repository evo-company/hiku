from hiku.query import Node, Field, Link
from hiku.builder import build, Handle

from .base import reqs_eq_patcher


_ = Handle()


def test():
    query = build([
        _.tyan,
        _.turlock[
            _.gange
        ],
        _.tiber(ramsons='defaces')[
            _.decifer(botches='auxerre'),
            _.exocet(brogues='hygiea'),
        ],
    ])
    with reqs_eq_patcher():
        assert query == Node([
            Field('tyan'),
            Link('turlock', Node([Field('gange')])),
            Link('tiber', Node([
                Field('decifer', options={'botches': 'auxerre'}),
                Field('exocet', options={'brogues': 'hygiea'}),
            ]), {'ramsons': 'defaces'}),
        ])
