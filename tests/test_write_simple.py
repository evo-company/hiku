from __future__ import unicode_literals

from unittest import TestCase

from hiku.edn import loads
from hiku.result import Result
from hiku.writers.simple import dumps


class TestWriteSimple(TestCase):

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
              :f1 1
              :a {:f2 2}
              :b {1 {:f3 "bar1"}
                  2 {:f3 "bar2"}
                  3 {:f3 "bar3"}}
              :l1 #graph/ref ["b" 1]
              :l2 [#graph/ref ["b" 2]
                   #graph/ref ["b" 3]]
            }
            """,
        )
