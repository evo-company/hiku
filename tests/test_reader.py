from unittest import TestCase

from hiku import reader
from hiku.edn import List, Keyword, Dict, TaggedElement, Tuple, Symbol


class TestReader(TestCase):

    def test(self):
        n = reader.read(b'[:foo {:bar [:baz]} (limit 10) '
                        b'#foo/uuid "678d88b2-87b0-403b-b63d-5da7465aecc3"]')
        self.assertEqual(n, List([
            Keyword('foo'),
            Dict({Keyword('bar'): List([Keyword('baz')])}),
            Tuple([Symbol('limit'), 10]),
            TaggedElement('foo/uuid', "678d88b2-87b0-403b-b63d-5da7465aecc3"),
        ]))
