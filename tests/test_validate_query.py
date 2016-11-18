import pytest

from hiku import query as q
from hiku.graph import Graph, Node, Field, Link, Option, Root
from hiku.types import Integer, Record, Sequence, Optional, TypeRef
from hiku.validate.query import QueryValidator


def _():
    return 1/0


GRAPH = Graph([
    Node('hooted', []),
    Root([
        Node('decants', []),

        # simple
        Field('robby', None, _),
        # complex
        Field('wounded', Optional[Record[{'attr': Integer}]], _),
        Field('annuals', Record[{'attr': Integer}], _),
        Field('hialeah', Sequence[Record[{'attr': Integer}]], _),
        # with options
        Field('motown', None, _, options=[Option('prine', None)]),
        Field('nyerere', None, _, options=[Option('epaule', None, default=1)]),
        Field('wreche', None, _, options=[Option('cierra', Integer)]),
        Field('hunter', None, _, options=[Option('fried', Integer, default=1)]),

        # simple
        Link('amyls', Sequence[TypeRef['hooted']], _, requires=None),
        # with options
        Link('ferrous', Sequence[TypeRef['hooted']], _, requires=None,
             options=[Option('cantab', None)]),
        Link('knesset', Sequence[TypeRef['hooted']], _, requires=None,
             options=[Option('ceases', None, default=1)]),
        Link('pouria', Sequence[TypeRef['hooted']], _, requires=None,
             options=[Option('flunk', Integer)]),
        Link('secants', Sequence[TypeRef['hooted']], _, requires=None,
             options=[Option('monadic', Integer, default=1)]),
    ]),
])


def check_errors(query, errors):
    validator = QueryValidator(GRAPH)
    validator.visit(query)
    assert validator.errors.list == errors


def test_field():
    # field in the root node
    check_errors(q.Node([q.Field('invalid')]), [
        'Field "invalid" is not implemented in the "root" node',
    ])
    # field in the global node
    check_errors(q.Node([q.Link('decants', q.Node([q.Field('invalid')]))]), [
        'Field "invalid" is not implemented in the "decants" node',
    ])
    # field in the linked node
    check_errors(q.Node([q.Link('amyls', q.Node([q.Field('invalid')]))]), [
        'Field "invalid" is not implemented in the "hooted" node',
    ])
    # simple field as node
    check_errors(q.Node([q.Link('robby', q.Node([]))]), [
        'Trying to query "root.robby" simple field as node',
    ])


@pytest.mark.parametrize('field_name', ['wounded', 'annuals', 'hialeah'])
def test_field_complex(field_name):
    check_errors(q.Node([q.Link(field_name, q.Node([]))]), [])
    check_errors(q.Node([q.Link(field_name, q.Node([q.Field('invalid')]))]), [
        'Unknown field name',
    ])
    check_errors(q.Node([q.Link(field_name, q.Node([q.Field('attr')]))]), [])


def test_non_field():
    check_errors(q.Node([q.Field('amyls')]), [
        'Trying to query "root.amyls" link as it was a field',
    ])
    check_errors(q.Node([q.Field('decants')]), [
        'Trying to query "decants" node as it was a field',
    ])


def test_field_options():
    def mk(field_name, **kwargs):
        return q.Node([q.Field(field_name, **kwargs)])

    check_errors(mk('motown'), [
        'Required option "root.motown:prine" is not specified',
    ])
    check_errors(mk('motown', options={}), [
        'Required option "root.motown:prine" is not specified',
    ])
    check_errors(mk('motown', options={'prine': 1}), [])
    check_errors(mk('motown', options={'prine': '1'}), [])
    check_errors(mk('motown', options={'prine': 1, 'invalid': 1}), [
        'Unknown options for "root.motown": invalid',
    ])

    check_errors(mk('nyerere'), [])
    check_errors(mk('nyerere', options={}), [])
    check_errors(mk('nyerere', options={'epaule': 1}), [])
    check_errors(mk('nyerere', options={'epaule': '1'}), [])
    check_errors(mk('nyerere', options={'epaule': 1, 'invalid': 1}), [
        'Unknown options for "root.nyerere": invalid',
    ])

    check_errors(mk('wreche'), [
        'Required option "root.wreche:cierra" is not specified',
    ])
    check_errors(mk('wreche', options={}), [
        'Required option "root.wreche:cierra" is not specified',
    ])
    check_errors(mk('wreche', options={'cierra': 1}), [])
    check_errors(mk('wreche', options={'cierra': '1'}), [
        'Invalid type "str" for option "root.wreche:cierra" provided',
    ])
    check_errors(mk('wreche', options={'cierra': 1, 'invalid': 1}), [
        'Unknown options for "root.wreche": invalid',
    ])

    check_errors(mk('hunter'), [])
    check_errors(mk('hunter', options={}), [])
    check_errors(mk('hunter', options={'fried': 1}), [])
    check_errors(mk('hunter', options={'fried': '1'}), [
        'Invalid type "str" for option "root.hunter:fried" provided',
    ])
    check_errors(mk('hunter', options={'fried': 1, 'invalid': 1}), [
        'Unknown options for "root.hunter": invalid',
    ])


def test_link():
    l = q.Link('invalid', q.Node([]))
    # link in the root node
    check_errors(q.Node([l]), [
        'Link "invalid" is not implemented in the "root" node',
    ])
    # link in the global node
    check_errors(q.Node([q.Link('decants', q.Node([l]))]), [
        'Link "invalid" is not implemented in the "decants" node',
    ])
    # link in the linked node
    check_errors(q.Node([q.Link('amyls', q.Node([l]))]), [
        'Link "invalid" is not implemented in the "hooted" node',
    ])


def test_link_options():
    def mk(link_name, **kwargs):
        return q.Node([q.Link(link_name, q.Node([]), **kwargs)])

    check_errors(mk('ferrous'), [
        'Required option "root.ferrous:cantab" is not specified',
    ])
    check_errors(mk('ferrous', options={}), [
        'Required option "root.ferrous:cantab" is not specified',
    ])
    check_errors(mk('ferrous', options={'cantab': 1}), [])
    check_errors(mk('ferrous', options={'cantab': '1'}), [])
    check_errors(mk('ferrous', options={'cantab': 1, 'invalid': 1}), [
        'Unknown options for "root.ferrous": invalid',
    ])

    check_errors(mk('knesset'), [])
    check_errors(mk('knesset', options={}), [])
    check_errors(mk('knesset', options={'ceases': 1}), [])
    check_errors(mk('knesset', options={'ceases': '1'}), [])
    check_errors(mk('knesset', options={'ceases': 1, 'invalid': 1}), [
        'Unknown options for "root.knesset": invalid',
    ])

    check_errors(mk('pouria'), [
        'Required option "root.pouria:flunk" is not specified',
    ])
    check_errors(mk('pouria', options={}), [
        'Required option "root.pouria:flunk" is not specified',
    ])
    check_errors(mk('pouria', options={'flunk': 1}), [])
    check_errors(mk('pouria', options={'flunk': '1'}), [
        'Invalid type "str" for option "root.pouria:flunk" provided',
    ])
    check_errors(mk('pouria', options={'flunk': 1, 'invalid': 1}), [
        'Unknown options for "root.pouria": invalid',
    ])

    check_errors(mk('secants'), [])
    check_errors(mk('secants', options={}), [])
    check_errors(mk('secants', options={'monadic': 1}), [])
    check_errors(mk('secants', options={'monadic': '1'}), [
        'Invalid type "str" for option "root.secants:monadic" provided',
    ])
    check_errors(mk('secants', options={'monadic': 1, 'invalid': 1}), [
        'Unknown options for "root.secants": invalid',
    ])
