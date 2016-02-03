import difflib
from textwrap import dedent

from hiku.graph import Edge, Field, Link
from hiku.typedef.kinko import dumps
from hiku.types import IntegerType, DictType, StringType
from hiku.types import ListType
from .base import TestCase


def noop(*args, **kwargs):
    raise NotImplementedError


class TestTypeDefKinko(TestCase):

    def assertDumps(self, root, schema):
        first = dumps(root)
        second = dedent(schema).strip() + '\n'
        if first != second:
            msg = ('Dumped schema mismatches:\n\n{}'
                   .format('\n'.join(difflib.ndiff(first.splitlines(),
                                                   second.splitlines()))))
            raise self.failureException(msg)

    def testField(self):
        self.assertDumps(
            Edge(None, [
                Field('A', noop),
            ]),
            """
            type A String
            """,
        )

    def testEdge(self):
        self.assertDumps(
            Edge(None, [
                Edge('Foo', [
                    Field('a', noop),
                    Field('c', noop),
                ]),
                Edge('Bar', [
                    Field('d', noop),
                    Field('b', noop),
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

    def testListSimple(self):
        f = Field('A', noop)
        f.type = ListType(IntegerType())
        self.assertDumps(
            Edge(None, [f]),
            """
            type A
              List Integer
            """,
        )

    def testListComplex(self):
        f = Field('A', noop)
        f.type = ListType(ListType(IntegerType()))
        self.assertDumps(
            Edge(None, [f]),
            """
            type A
              List
                List Integer
            """,
        )

    def testDictSimple(self):
        f = Field('A', noop)
        f.type = DictType(StringType(), IntegerType())
        self.assertDumps(
            Edge(None, [f]),
            """
            type A
              Dict String Integer
            """,
        )

    def testDictComplex(self):
        f = Field('A', noop)
        f.type = DictType(StringType(),
                          DictType(IntegerType(), IntegerType()))
        self.assertDumps(
            Edge(None, [f]),
            """
            type A
              Dict String
                Dict Integer Integer
            """,
        )

    def testTypeRef(self):
        self.assertDumps(
            Edge(None, [
                Edge('Foo', [
                    Field('a', noop),
                ]),
                Edge('Bar', [
                    Field('b', noop),
                    Link('c', None, 'Foo', noop, to_list=False),
                ]),
                Edge('Baz', [
                    Field('d', noop),
                    Link('e', None, 'Foo', noop, to_list=True),
                ]),
            ]),
            """
            type Foo
              Record
                :a String

            type Bar
              Record
                :b String
                :c Foo

            type Baz
              Record
                :d String
                :e
                  List Foo
            """,
        )
