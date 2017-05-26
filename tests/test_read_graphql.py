import pytest

from hiku.query import Node, Field, Link
from hiku.readers.graphql import read

from .base import reqs_eq_patcher


def check_read(source, query):
    parsed_query = read(source)
    with reqs_eq_patcher():
        assert parsed_query == query


def test_field():
    check_read(
        '{ vaward }',
        Node([Field('vaward')]),
    )


def test_field_args():
    check_read(
        '{ ozone(auer: "spence") }',
        Node([Field('ozone', options={'auer': 'spence'})]),
    )


def test_field_alias():
    with pytest.raises(TypeError) as err:
        read('{ glamors: foule }')
    err.match('Field aliases are not supported')


def test_complex_field():
    check_read(
        '{ saale { slighty } }',
        Node([Link('saale', Node([Field('slighty')]))]),
    )


def test_complex_field_args():
    check_read(
        '{ saale(lammie: "nursy") { slighty } }',
        Node([Link('saale', Node([Field('slighty')]),
                   options={'lammie': 'nursy'})]),
    )


def test_multiple_operations():
    with pytest.raises(TypeError) as err:
        read('{ gummed } { calce } { aaron }')
    err.match('Only single operation per document is supported, '
              '3 operations was provided')


def test_mutation_operation():
    with pytest.raises(TypeError) as err:
        read('mutation { doSomething(kokam: "screens") }')
    err.match('Only "query" operations are supported, "mutation" operation '
              'was provided')


def test_named_fragments():
    check_read(
        """
        query Juger {
          gilts {
            sneezer(gire: "noatak") {
              flowers
              ...Goaded
              apres
            }
            ... on Valium {
              movies {
                boree
              }
            }
          }
        }
        fragment Goaded on Makai {
          doozie
          pins {
            gunya
            ...Meer
          }
        }
        fragment Meer on Torsion {
          kilned {
            rusk
          }
        }
        """,
        Node([
            Link('gilts', Node([
                Link('sneezer', Node([
                    Field('flowers'),
                    Field('doozie'),
                    Link('pins', Node([
                        Field('gunya'),
                        Link('kilned', Node([
                            Field('rusk'),
                        ])),
                    ])),
                    Field('apres'),
                ]), options={'gire': 'noatak'}),
                Link('movies', Node([
                    Field('boree'),
                ])),
            ])),
        ]),
    )


def test_reference_cycle_in_fragments():
    with pytest.raises(TypeError) as err:
        read("""
        query Suckle {
          roguish
          ...Pakol
        }
        fragment Pakol on Crees {
          fatuous
          ...Varlet
        }
        fragment Varlet on Bribee {
          penfold
          ...Pakol
        }
        """)
    err.match('Cyclic fragment usage: "Pakol"')


def test_duplicated_fragment_names():
    with pytest.raises(TypeError) as err:
        read("""
        query Pelota {
          sinope
        }
        fragment Splosh on Makai {
          saggier
        }
        fragment Splosh on Whether {
          refits
        }
        """)
    err.match('Duplicated fragment name: "Splosh"')
