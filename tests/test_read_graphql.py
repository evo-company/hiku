from hiku.query import Edge, Field
from hiku.readers.graphql import read

from .base import TestCase, reqs_eq_patcher


class TestReadGraphQL(TestCase):

    def test(self):
        with reqs_eq_patcher():
            self.assertEqual(
                read("""
                { hello }
                """),
                Edge([Field('hello')]),
            )
