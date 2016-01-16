from __future__ import unicode_literals

from unittest import TestCase

from hiku.edn import loads, dumps
from hiku.edn import List, Keyword, Dict, TaggedElement, Tuple, Symbol


class TestEDN(TestCase):

    def testLoads(self):
        n = loads('[:foo {:bar [:baz]} (limit 10) '
                  '#foo/uuid "678d88b2-87b0-403b-b63d-5da7465aecc3"]')
        self.assertEqual(n, List([
            Keyword('foo'),
            Dict({Keyword('bar'): List([Keyword('baz')])}),
            Tuple([Symbol('limit'), 10]),
            TaggedElement('foo/uuid', "678d88b2-87b0-403b-b63d-5da7465aecc3"),
        ]))

    def testTaggedElement(self):
        self.assertEqual(
            dumps(TaggedElement('foo/bar', 'baz')),
            '#foo/bar "baz"',
        )
