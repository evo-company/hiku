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
    with pytest.raises(NotImplementedError) as err:
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
    with pytest.raises(NotImplementedError) as err:
        read('{ gummed } { calce } { aaron }')
    err.match('Only single operation per document is supported, '
              '3 operations was provided')


def test_mutation_operation():
    with pytest.raises(NotImplementedError) as err:
        read('mutation { doSomething(kokam: "screens") }')
    err.match('Only "query" operations are supported, "mutation" operation '
              'was provided')


def test_unknown_node():
    with pytest.raises(NotImplementedError) as err:
        read('fragment bays on sweats { apollo }')
    err.match('Not implemented node type: FragmentDefinition')
