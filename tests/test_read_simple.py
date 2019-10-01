import pytest

from hiku.query import Node, Field, Link
from hiku.readers.simple import read


def check_read(source, query):
    first = read(source)
    assert first == query


def test_invalid_root():
    with pytest.raises(TypeError):
        read('{:foo []}')
    with pytest.raises(TypeError):
        read(':foo')


def test_field():
    check_read(
        """
        [:foo :bar]
        """,
        Node([Field('foo'), Field('bar')]),
    )


def test_field_invalid():
    with pytest.raises(TypeError):
        read('["foo"]')
    with pytest.raises(TypeError):
        read('[1]')


def test_field_options():
    check_read(
        """
        [(:foo {:bar 1}) :baz]
        """,
        Node([Field('foo', options={'bar': 1}),
              Field('baz')]),
    )


def test_field_invalid_options():
    # missing options
    with pytest.raises(TypeError):
        read('[(:foo)]')

    # invalid options type
    with pytest.raises(TypeError):
        read('[(:foo :bar)]')

    # more arguments than expected
    with pytest.raises(TypeError):
        read('[(:foo 1 2)]')

    # invalid option key
    with pytest.raises(TypeError):
        read('[(:foo {1 2})]')


def test_link():
    check_read(
        """
        [{:foo [:bar :baz]}]
        """,
        Node([Link('foo', Node([Field('bar'), Field('baz')]))]),
    )


def test_link_options():
    check_read(
        """
        [{(:foo {:bar 1}) [:baz]}]
        """,
        Node([Link('foo', Node([Field('baz')]),
                   options={'bar': 1})]),
    )


def test_link_invalid():
    with pytest.raises(TypeError):
        read('[{"foo" [:baz]}]')
    with pytest.raises(TypeError):
        read('[{foo [:baz]}]')


def test_link_invalid_options():
    # missing options
    with pytest.raises(TypeError):
        read('[{(:foo) [:baz]}]')

    # invalid options type
    with pytest.raises(TypeError):
        read('[{(:foo :bar) [:baz]}]')

    # more arguments than expected
    with pytest.raises(TypeError):
        read('[{(:foo 1 2) [:bar]}]')

    # invalid option key
    with pytest.raises(TypeError):
        read('[{(:foo {1 2}) [:bar]}]')
