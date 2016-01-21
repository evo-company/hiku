from __future__ import unicode_literals

from json import loads

from unittest import TestCase

from hiku.store import Store
from hiku.writers.json import dumps


class TestWriteJSON(TestCase):

    def assertWrites(self, data, output):
        first = loads(dumps(data))
        second = loads(output)
        self.assertEqual(first, second)

    def testSimple(self):
        store = Store()
        store['f1'] = 1
        store['a']['f2'] = 2
        store.idx['b'][1] = {'f3': 'bar1'}
        store.idx['b'][2] = {'f3': 'bar2'}
        store.idx['b'][3] = {'f3': 'bar3'}
        store['l1'] = store.ref('b', 1)
        store['l2'] = [store.ref('b', 2), store.ref('b', 3)]
        self.assertWrites(
            store,
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
