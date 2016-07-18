import difflib
from textwrap import dedent

from hiku.graph import Graph, Edge, Field, Link, Root, Many, One
from hiku.types import Sequence, Mapping, Integer, String, Optional
from hiku.typedef.kinko import dumps

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
            Graph([Root([
                Field('A', String, noop),
            ])]),
            """
            type A String
            """,
        )

    def testEdge(self):
        self.assertDumps(
            Graph([
                Edge('Foo', [
                    Field('a', String, noop),
                    Field('c', String, noop),
                ]),
                Edge('Bar', [
                    Field('d', String, noop),
                    Field('b', String, noop),
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
            Graph([Root([
                Field('A', Sequence[Integer], noop),
            ])]),
            """
            type A
              List Integer
            """,
        )

    def testListComplex(self):
        self.assertDumps(
            Graph([Root([
                Field('A', Sequence[Sequence[Integer]], noop),
            ])]),
            """
            type A
              List
                List Integer
            """,
        )

    def testDictSimple(self):
        self.assertDumps(
            Graph([Root([
                Field('A', Mapping[String, Integer], noop),
            ])]),
            """
            type A
              Dict String Integer
            """,
        )

    def testDictComplex(self):
        self.assertDumps(
            Graph([Root([
                Field('A', Mapping[String, Mapping[Integer, Integer]],
                      noop),
            ])]),
            """
            type A
              Dict String
                Dict Integer Integer
            """,
        )

    def testTypeRef(self):
        self.assertDumps(
            Graph([
                Edge('Foo', [
                    Field('a', String, noop),
                ]),
                Edge('Bar', [
                    Field('b', String, noop),
                    Link('c', One, noop, edge='Foo', requires=None),
                ]),
                Edge('Baz', [
                    Field('d', String, noop),
                    Link('e', Many, noop, edge='Foo', requires=None),
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
            Graph([
                Edge('Foo', [
                    Field('a', String, noop, description="Attribute a"),
                ], description="Some Foo explanation"),
                Edge('Bar', [
                    Field('b', Optional[String], noop,
                          description="Attribute b"),
                    Link('c', One, noop, edge='Foo', requires=None,
                         description="Link c to Foo"),
                ], description="Some Bar explanation"),
                Edge('Baz', [
                    Field('d', String, noop, description="Attribute d"),
                    Link('e', Many, noop, edge='Foo', requires=None,
                         description="Link e to Foo"),
                ], description="Some Baz explanation"),
            ]),
            """
            type Foo  ; Some Foo explanation
              Record
                :a String  ; Attribute a

            type Bar  ; Some Bar explanation
              Record
                :b  ; Attribute b
                  Option String
                :c Foo  ; Link c to Foo

            type Baz  ; Some Baz explanation
              Record
                :d String  ; Attribute d
                :e  ; Link e to Foo
                  List Foo
            """,
        )
