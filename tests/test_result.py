from __future__ import unicode_literals

import json

from hiku.graph import Graph, Link, Edge, Field
from hiku.result import denormalize, Result
from hiku.readers.simple import read

from .base import TestCase


def noop():
    return 1/0


class TestDenormalize(TestCase):

    def setUp(self):
        self.graph = Graph([
            Edge('x', [
                Field('id', noop),
                Field('a', noop),
                Field('b', noop),
                Link('y1', noop, to='y', requires='id', to_list=False),
            ]),
            Edge('y', [
                Field('id', noop),
                Field('c', noop),
                Field('d', noop),
                Link('xs', noop, to='x', requires='id', to_list=True),
            ]),
            Link('xs', noop, to='x', requires=None, to_list=True),
            Link('y1', noop, to='y', requires=None, to_list=False),
            Edge('z', [
                Field('e', noop),
                Link('y1', noop, to='y', requires=None, to_list=False),
                Link('xs', noop, to='x', requires=None, to_list=True),
            ]),
        ])
        self.result = Result()
        self.result.idx['x'][1] = {
            'a': 1,
            'b': 2,
            'y1': self.result.ref('y', 3),
        }
        self.result.idx['x'][2] = {
            'a': 3,
            'b': 4,
            'y1': self.result.ref('y', 3),
        }
        self.result.idx['y'][3] = {
            'c': 3,
            'd': 4,
            'xs': [
                self.result.ref('x', 1),
                self.result.ref('x', 2),
            ],
        }
        self.result['xs'] = [self.result.ref('x', 2), self.result.ref('x', 1)]
        self.result['y1'] = self.result.ref('y', 3)
        self.result['z'] = {
            'e': 5,
            'y1': self.result.ref('y', 3),
            'xs': [self.result.ref('x', 1), self.result.ref('x', 2)],
        }

    def check_denormalize(self, query_string, result):
        new_result = denormalize(self.graph, self.result, read(query_string))
        json.dumps(new_result)  # json checks for circular references
        self.assertEqual(
            new_result,
            result,
        )

    def testSingleEdge(self):
        self.check_denormalize(
            '[{:z [:e {:y1 [:c]} {:xs [:b]}]}]',
            {'z': {'e': 5,
                   'y1': {'c': 3},
                   'xs': [{'b': 2}, {'b': 4}]}},
        )

    def testLinkOne(self):
        self.check_denormalize(
            '[{:y1 [:c :d]}]',
            {'y1': {'c': 3, 'd': 4}},
        )

    def testLinkMany(self):
        self.check_denormalize(
            '[{:xs [:a :b]}]',
            {'xs': [{'a': 3, 'b': 4}, {'a': 1, 'b': 2}]},
        )

    def testLinkOneWithLinkMany(self):
        self.check_denormalize(
            '[{:y1 [:c :d {:xs [:a :b]}]}]',
            {'y1': {'c': 3, 'd': 4,
                    'xs': [{'a': 1, 'b': 2},
                           {'a': 3, 'b': 4}]}},
        )

    def testLinkManyWithLinkOne(self):
        self.check_denormalize(
            '[{:xs [:a :b {:y1 [:c :d]}]}]',
            {'xs': [{'a': 3, 'b': 4, 'y1': {'c': 3, 'd': 4}},
                    {'a': 1, 'b': 2, 'y1': {'c': 3, 'd': 4}}]},
        )

    def testLinkOneCircle(self):
        self.check_denormalize(
            '[{:y1 [:c {:xs [:a :b {:y1 [:d]}]}]}]',
            {'y1': {'c': 3,
                    'xs': [{'a': 1, 'b': 2, 'y1': {'d': 4}},
                           {'a': 3, 'b': 4, 'y1': {'d': 4}}]}},
        )

    def testLinkManyCircle(self):
        self.check_denormalize(
            '[{:xs [:a {:y1 [:c :d {:xs [:b]}]}]}]',
            {'xs': [{'a': 3, 'y1': {'c': 3, 'd': 4,
                                    'xs': [{'b': 2}, {'b': 4}]}},
                    {'a': 1, 'y1': {'c': 3, 'd': 4,
                                    'xs': [{'b': 2}, {'b': 4}]}}]},
        )
