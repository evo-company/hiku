from hiku.query import merge, Node, Field, Link

from .base import TestCase, reqs_eq_patcher


class TestMerge(TestCase):

    def test(self):
        with reqs_eq_patcher():
            self.assertEqual(
                merge([
                    Node([Field('a1'), Field('a2'),
                          Link('b', Node([Field('b1'), Field('b2')]))]),
                    Node([Field('a2'), Field('a3'),
                          Link('b', Node([Field('b2'), Field('b3')]))]),
                ]),
                Node([Field('a1'), Field('a2'), Field('a3'),
                      Link('b', Node([Field('b1'), Field('b2'),
                                      Field('b3')]))]),
            )
