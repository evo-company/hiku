from hiku.query import Node, Field
from hiku.readers.graphql import read

from .base import TestCase, reqs_eq_patcher


class TestReadGraphQL(TestCase):

    def test(self):
        with reqs_eq_patcher():
            self.assertEqual(
                read("""
                { hello }
                """),
                Node([Field('hello')]),
            )
