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
                Field('A', StringType, noop),
            ]),
            """
            type A String
            """,
        )

    def testEdge(self):
        self.assertDumps(
            Edge(None, [
                Edge('Foo', [
                    Field('a', StringType, noop),
                    Field('c', StringType, noop),
                ]),
                Edge('Bar', [
                    Field('d', StringType, noop),
                    Field('b', StringType, noop),
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
        self.assertDumps(
            Edge(None, [
                Field('A', ListType(IntegerType), noop),
            ]),
            """
            type A
              List Integer
            """,
        )

    def testListComplex(self):
        self.assertDumps(
            Edge(None, [
                Field('A', ListType(ListType(IntegerType)), noop),
            ]),
            """
            type A
              List
                List Integer
            """,
        )

    def testDictSimple(self):
        self.assertDumps(
            Edge(None, [
                Field('A', DictType(StringType, IntegerType), noop),
            ]),
            """
            type A
              Dict String Integer
            """,
        )

    def testDictComplex(self):
        self.assertDumps(
            Edge(None, [
                Field('A', DictType(StringType,
                                    DictType(IntegerType, IntegerType)),
                      noop),
            ]),
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
                    Field('a', StringType, noop),
                ]),
                Edge('Bar', [
                    Field('b', StringType, noop),
                    Link('c', None, 'Foo', noop, to_list=False),
                ]),
                Edge('Baz', [
                    Field('d', StringType, noop),
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

    def testDocs(self):
        self.assertDumps(
            Edge(None, [
                Edge('Foo', [
                    Field('a', StringType, noop, doc="Attribute a"),
                ], doc="Some Foo explanation"),
                Edge('Bar', [
                    Field('b', StringType, noop, doc="Attribute b"),
                    Link('c', None, 'Foo', noop, to_list=False,
                         doc="Link c to Foo"),
                ], doc="Some Bar explanation"),
                Edge('Baz', [
                    Field('d', StringType, noop, doc="Attribute d"),
                    Link('e', None, 'Foo', noop, to_list=True,
                         doc="Link e to Foo"),
                ], doc="Some Baz explanation"),
            ]),
            """
            type Foo  ; Some Foo explanation
              Record
                :a String  ; Attribute a

            type Bar  ; Some Bar explanation
              Record
                :b String  ; Attribute b
                :c Foo  ; Link c to Foo

            type Baz  ; Some Baz explanation
              Record
                :d String  ; Attribute d
                :e  ; Link e to Foo
                  List Foo
            """,
        )
