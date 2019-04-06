import pytest

from graphql.language import ast
from graphql.language.parser import parse

from hiku.query import Node, Field, Link
from hiku.readers.graphql import read, OperationGetter
from hiku.readers.graphql import read_operation, OperationType


def check_read(source, query, variables=None):
    parsed_query = read(source, variables)
    assert parsed_query == query


def test_operation_getter_no_ops():
    with pytest.raises(TypeError) as err:
        OperationGetter.get(parse('fragment Foo on Bar { id }'))
    err.match('No operations in the document')


def test_operation_getter_no_name():
    query = OperationGetter.get(parse('{ foo }'))
    assert query.name is None
    assert query.operation is ast.OperationType.QUERY

    named_query = OperationGetter.get(parse('query Foo { foo }'))
    assert named_query.name.value == 'Foo'
    assert named_query.operation is ast.OperationType.QUERY

    mutation = OperationGetter.get(parse('mutation Foo { foo }'), None)
    assert mutation.name.value == 'Foo'
    assert mutation.operation is ast.OperationType.MUTATION

    with pytest.raises(TypeError) as err:
        OperationGetter.get(parse('query Foo { foo } query Bar { bar }'))
    err.match('Document should contain exactly one operation')


def test_operation_getter_duplicates():
    with pytest.raises(TypeError) as e1:
        OperationGetter.get(parse('{ foo } { bar }'))
    assert e1.match('Duplicate operation definition: None')

    with pytest.raises(TypeError) as e2:
        OperationGetter.get(parse('query Foo { foo } query Foo { bar }'))
    assert e2.match('Duplicate operation definition: {!r}'.format('Foo'))


def test_operation_getter_by_name():
    q1 = OperationGetter.get(parse('query Foo { foo } query Bar { bar }'),
                             'Bar')
    assert q1.name.value == 'Bar'
    assert q1.operation is ast.OperationType.QUERY

    q2 = OperationGetter.get(parse('query Foo { foo } mutation Bar { bar }'),
                             'Bar')
    assert q2.operation is ast.OperationType.MUTATION


def test_field():
    check_read(
        '{ vaward }',
        Node([Field('vaward')]),
    )


def test_field_args():
    check_read(
        '{ ozone(auer: 123) }',
        Node([Field('ozone', options={'auer': 123})]),
    )
    check_read(
        '{ ozone(auer: 234.5) }',
        Node([Field('ozone', options={'auer': pytest.approx(234.5)})]),
    )
    check_read(
        '{ ozone(auer: "spence") }',
        Node([Field('ozone', options={'auer': 'spence'})]),
    )
    check_read(
        '{ ozone(auer: true) }',
        Node([Field('ozone', options={'auer': True})]),
    )
    check_read(
        '{ ozone(auer: null) }',
        Node([Field('ozone', options={'auer': None})]),
    )
    check_read(
        '{ ozone(auer: HURTEST) }',
        Node([Field('ozone', options={'auer': 'HURTEST'})]),
    )
    check_read(
        '{ ozone(auer: [345, true, "platies"]) }',
        Node([Field('ozone', options={'auer': [345, True, 'platies']})]),
    )
    check_read(
        '{ ozone(auer: {pooted: 456, wassup: "whir"}) }',
        Node([Field('ozone', options={'auer': {'pooted': 456,
                                               'wassup': 'whir'}})]),
    )
    check_read(
        '{ ozone(auer: [1, {abasing: [2, 3]}, 4]) }',
        Node([Field('ozone', options={'auer': [1, {'abasing': [2, 3]}, 4]})]),
    )


def test_field_alias():
    check_read(
        '{ a: b }',
        Node([Field('b', alias='a')]),
    )


def test_link_alias():
    check_read(
        '{ a: b { c d } }',
        Node([
            Link('b', Node([
                Field('c'),
                Field('d'),
            ]), alias='a'),
        ]),
    )


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
    err.match('Duplicate operation definition: None')


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
                    Field('apres'),
                    Link('pins', Node([
                        Field('gunya'),
                        Link('kilned', Node([
                            Field('rusk'),
                        ])),
                    ])),
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


def test_variables_in_query():
    check_read(
        """
        query Milks($oba: Int, $barwin: Int!, $alpacas: Int! = 123) {
          inlined(crapper: $oba, finn: $barwin, buccina: $alpacas)
        }
        """,
        Node([Field('inlined',
                    options={'crapper': None, 'finn': 123, 'buccina': 123})]),
        {'barwin': 123},
    )


def test_variables_in_fragment():
    check_read(
        """
        query Jester($pushy: Int, $popedom: Int!, $tookies: Int! = 234) {
          ...Pujari
        }

        fragment Pujari on Ashlee {
          fibbery(baps: $pushy, bankit: $popedom, riuer: $tookies)
        }
        """,
        Node([Field('fibbery',
                    options={'baps': None, 'bankit': 123, 'riuer': 234})]),
        {'popedom': 123},
    )


def test_undefined_variables():
    with pytest.raises(TypeError) as err:
        read("""
        {
          selma(djin: $geeky)
        }
        """)
    err.match(r'Variable \$geeky is not defined in query <unnamed>')

    with pytest.raises(TypeError) as err:
        read("""
        query Oriolus {
          ve(sac: $bd)
        }
        """)
    err.match(r'Variable \$bd is not defined in query Oriolus')

    with pytest.raises(TypeError) as err:
        read("""
        query Had {
          ...Fulgent
        }

        fragment Fulgent on Ashlee {
          chewie(newton: $aliyah)
        }
        """)
    err.match(r'Variable \$aliyah is not defined in query Had')


def test_missing_variables():
    with pytest.raises(TypeError) as err:
        read("""
        query Belinda($asides: Int!) {
          ebonics
        }
        """)
    err.match('Variable "asides" is not provided for query Belinda')


def test_read_operation_query():
    op = read_operation('query { pong }')
    assert op.type is OperationType.QUERY
    assert op.query == Node([Field('pong')])


def test_read_operation_mutation():
    op = read_operation('mutation { ping }')
    assert op.type is OperationType.MUTATION
    assert op.query == Node([Field('ping')], ordered=True)


def test_read_operation_subscription():
    op = read_operation('subscription { ping }')
    assert op.type is OperationType.SUBSCRIPTION
    assert op.query == Node([Field('ping')])
