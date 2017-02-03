from __future__ import unicode_literals

from hiku.graph import Graph, Root, Field, Node, Link
from hiku.types import String, Integer, TypeRef, Sequence
from hiku.result import Result
from hiku.readers.simple import read
from hiku.writers.protobuf import populate

from .protobuf import jowk_pb2 as t


def _(*args):
    raise NotImplementedError('Data loading not implemented')


GRAPH = Graph([
    Node('Synocha', [
        Field('grovel', Integer, _),
        Field('chaddar', String, _),
    ]),
    Node('Estufa', [
        Field('bald', Integer, _),
        Field('tandoor', String, _),
        Link('specify', Sequence[TypeRef['Synocha']], _, requires=None),
    ]),
    Root([
        Link('soberly', TypeRef['Estufa'], _, requires=None),
        Field('snarfs', String, _),
    ]),
])


def check_pb(simple_query, result, expected):
    pb_root = t.Root()
    populate(pb_root, GRAPH, result, read(simple_query))
    assert pb_root == expected


def test_root_field():
    result = Result()
    result.root = {'snarfs': 'chis'}

    pb_root = t.Root()
    pb_root.snarfs = 'chis'

    check_pb('[:snarfs]', result, pb_root)


def test_root_link():
    result = Result()
    result.root = {'soberly': result.ref('Estufa', 1)}
    result.index.update({'Estufa': {1: {'tandoor': 'magot'}}})

    pb_root = t.Root()
    pb_root.soberly.tandoor = 'magot'

    check_pb('[{:soberly [:tandoor]}]', result, pb_root)
