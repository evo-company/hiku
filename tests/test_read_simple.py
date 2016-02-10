from __future__ import unicode_literals

from hiku.query import Edge, Field, Link
from hiku.readers.simple import read

from .base import TestCase, reqs_eq_patcher


class TestReadSimple(TestCase):

    def assertReads(self, source, query):
        first = read(source)
        with reqs_eq_patcher():
            self.assertEqual(first, query)

    def testInvalidRoot(self):
        with self.assertRaises(TypeError):
            read('{:foo []}')
        with self.assertRaises(TypeError):
            read(':foo')

    def testField(self):
        self.assertReads(
            """
            [:foo :bar]
            """,
            Edge([Field('foo'), Field('bar')]),
        )

    def testFieldInvalid(self):
        with self.assertRaises(TypeError):
            read('["foo"]')
        with self.assertRaises(TypeError):
            read('[1]')

    def testFieldOptions(self):
        self.assertReads(
            """
            [(:foo {:bar 1}) :baz]
            """,
            Edge([Field('foo', options={'bar': 1}),
                  Field('baz')]),
        )

    def testFieldInvalidOptions(self):
        # missing options
        with self.assertRaises(TypeError):
            read('[(:foo)]')

        # invalid options type
        with self.assertRaises(TypeError):
            read('[(:foo :bar)]')

        # more arguments than expected
        with self.assertRaises(TypeError):
            read('[(:foo 1 2)]')

        # invalid option key
        with self.assertRaises(TypeError):
            read('[(:foo {1 2})]')

    def testLink(self):
        self.assertReads(
            """
            [{:foo [:bar :baz]}]
            """,
            Edge([Link('foo', Edge([Field('bar'), Field('baz')]))]),
        )

    def testLinkOptions(self):
        self.assertReads(
            """
            [{(:foo {:bar 1}) [:baz]}]
            """,
            Edge([Link('foo', Edge([Field('baz')]),
                       options={'bar': 1})]),
        )

    def testLinkInvalid(self):
        with self.assertRaises(TypeError):
            read('[{"foo" [:baz]}]')
        with self.assertRaises(TypeError):
            read('[{foo [:baz]}]')

    def testLinkInvalidOptions(self):
        # missing options
        with self.assertRaises(TypeError):
            read('[{(:foo) [:baz]}]')

        # invalid options type
        with self.assertRaises(TypeError):
            read('[{(:foo :bar) [:baz]}]')

        # more arguments than expected
        with self.assertRaises(TypeError):
            read('[{(:foo 1 2) [:bar]}]')

        # invalid option key
        with self.assertRaises(TypeError):
            read('[{(:foo {1 2}) [:bar]}]')
