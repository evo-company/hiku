from __future__ import unicode_literals

from hiku.edn import loads, dumps
from hiku.edn import List, Keyword, Dict, TaggedElement, Tuple, Symbol


def test_symbol():
    assert loads('foo') == Symbol('foo')


def test_nil():
    assert loads('[1 nil 2]') == List([1, None, 2])


def test_loads():
    n = loads('[:foo {:bar [:baz]} (limit 10) '
              '#foo/uuid "678d88b2-87b0-403b-b63d-5da7465aecc3"]')
    assert n == List([
        Keyword('foo'),
        Dict({Keyword('bar'): List([Keyword('baz')])}),
        Tuple([Symbol('limit'), 10]),
        TaggedElement('foo/uuid', "678d88b2-87b0-403b-b63d-5da7465aecc3"),
    ])


def test_tagged_element():
    assert dumps(TaggedElement('foo/bar', 'baz')) == '#foo/bar "baz"'
