from __future__ import unicode_literals

from json import loads

from unittest import TestCase

from hiku.result import Result
from hiku.writers.json import dumps


class TestWriteJSON(TestCase):

    def assertWrites(self, data, output):
        first = loads(dumps(data))
        second = loads(output)
        self.assertEqual(first, second)

    def testSimple(self):
        result = Result()
        result['f1'] = 1
        result['a']['f2'] = 2
        result.idx['b'][1] = {'f3': 'bar1'}
        result.idx['b'][2] = {'f3': 'bar2'}
        result.idx['b'][3] = {'f3': 'bar3'}
        result['l1'] = result.ref('b', 1)
        result['l2'] = [result.ref('b', 2), result.ref('b', 3)]
        self.assertWrites(
            result,
            """
            {
              "f1": 1,
              "a": {"f2": 2},
              "l1": {"f3": "bar1"},
              "l2": [
                {"f3": "bar2"},
                {"f3": "bar3"}
              ]
            }
            """,
        )
