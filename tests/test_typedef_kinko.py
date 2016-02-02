import difflib
from textwrap import dedent

from hiku.graph import Edge, Field
from hiku.typedef.kinko import dumps

from .base import TestCase


class TestTypeDefKinko(TestCase):

    def assertDumps(self, root, schema):
        first = dumps(root)
        second = dedent(schema).strip() + '\n'
        if first != second:
            msg = ('Dumped schema mismatches:\n\n{}'
                   .format('\n'.join(difflib.ndiff(first.splitlines(),
                                                   second.splitlines()))))
            raise self.failureException(msg)

    def test(self):
        self.assertDumps(
            Edge(None, [
                Edge('Foo', [
                    Field('a', lambda: 1/0),
                    Field('c', lambda: 1/0),
                ]),
                Edge('Bar', [
                    Field('d', lambda: 1/0),
                    Field('b', lambda: 1/0),
                ]),
            ]),
            """
            type Foo
              Record
                :a String
                :c String

            type Bar
              Record
                :d String
                :b String
            """,
        )
