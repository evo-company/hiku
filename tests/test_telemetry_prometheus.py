import time

import faker
import pytest

from prometheus_client import REGISTRY

from hiku import query as q
from hiku.expr.core import S
from hiku.expr.core import define
from hiku.graph import Graph, Node, Field, Link, Root, apply
from hiku.telemetry.prometheus import GraphMetricsNew
from hiku.types import Any
from hiku.types import TypeRef
from hiku.engine import Engine, pass_context
from hiku.sources.graph import SubGraph
from hiku.executors.sync import SyncExecutor
from hiku.executors.asyncio import AsyncIOExecutor
from hiku.telemetry.prometheus import GraphMetrics, AsyncGraphMetrics
from hiku.utils import listify

from tests.base import check_result


fake = faker.Faker()


@pytest.fixture(name='graph_name')
def graph_name_fixture():
    return fake.pystr()


@pytest.fixture(name='sample_count')
def sample_count_fixture(graph_name):
    def sample_count(node, field):
        REGISTRY.get_sample_value(
            'graph_field_time_count',
            dict(graph=graph_name, node=node, field=field),
        )
    return sample_count


@pytest.fixture(name='sample_sum')
def sample_sum_fixture(graph_name):
    def sample_count(node, field):
        value = REGISTRY.get_sample_value(
            'graph_field_time_sum',
            dict(graph=graph_name, node=node, field=field),
        )
        print('{}.{}, value: {}'.format(node, field, value))
        return value
    return sample_count


def test_simple_sync(graph_name, sample_count):

    def x_fields(fields, ids):
        return [[42 for _ in fields] for _ in ids]

    def root_fields(fields):
        return [1 for _ in fields]

    def x_link():
        return 2

    ll_graph = Graph([
        Node('X', [
            Field('id', None, x_fields),
        ]),
    ])

    x_sg = SubGraph(ll_graph, 'X')

    hl_graph = Graph([
        Node('X', [
            Field('id', None, x_sg),
        ]),
        Root([
            Field('a', None, root_fields),
            Link('x', TypeRef['X'], x_link, requires=None),
        ]),
    ])

    hl_graph = apply(hl_graph, [GraphMetrics(graph_name)])

    assert sample_count('Root', 'a') is None
    assert sample_count('Root', 'x') is None
    assert sample_count('X', 'id') is None

    result = Engine(SyncExecutor()).execute(hl_graph, q.Node([
        q.Field('a'),
        q.Link('x', q.Node([
            q.Field('id'),
        ])),
    ]))
    check_result(result, {
        'a': 1,
        'x': {
            'id': 42,
        },
    })

    assert sample_count('Root', 'a') == 1.0
    assert sample_count('Root', 'x') == 1.0
    assert sample_count('X', 'id') == 1.0


@pytest.mark.asyncio
async def test_simple_async(graph_name, sample_count):

    async def x_fields(fields, ids):
        return [[42 for _ in fields] for _ in ids]

    async def root_fields(fields):
        return [1 for _ in fields]

    async def x_link():
        return 2

    ll_graph = Graph([
        Node('X', [
            Field('id', None, x_fields),
        ]),
    ])

    x_sg = SubGraph(ll_graph, 'X')

    hl_graph = Graph([
        Node('X', [
            Field('id', None, x_sg),
        ]),
        Root([
            Field('a', None, root_fields),
            Link('x', TypeRef['X'], x_link, requires=None),
        ]),
    ])

    hl_graph = apply(hl_graph, [AsyncGraphMetrics(graph_name)])

    query = q.Node([
        q.Field('a'),
        q.Link('x', q.Node([
            q.Field('id'),
        ])),
    ])

    engine = Engine(AsyncIOExecutor())

    assert sample_count('Root', 'a') is None
    assert sample_count('Root', 'x') is None
    assert sample_count('X', 'id') is None

    result = await engine.execute(hl_graph, query)
    check_result(result, {
        'a': 1,
        'x': {
            'id': 42,
        },
    })

    assert sample_count('Root', 'a') == 1.0
    assert sample_count('Root', 'x') == 1.0
    assert sample_count('X', 'id') == 1.0


def test_with_pass_context(graph_name, sample_count):

    def root_fields1(fields):
        return [1 for _ in fields]

    @pass_context
    def root_fields2(ctx, fields):
        return [2 for _ in fields]

    graph = Graph([
        Root([
            Field('a', None, root_fields1),
            Field('b', None, root_fields2),
        ]),
    ])

    graph = apply(graph, [GraphMetrics(graph_name)])

    assert sample_count('Root', 'a') is None
    assert sample_count('Root', 'b') is None

    result = Engine(SyncExecutor()).execute(graph, q.Node([
        q.Field('a'),
        q.Field('b'),
    ]))
    check_result(result, {
        'a': 1,
        'b': 2,
    })

    assert sample_count('Root', 'a') == 1.0
    assert sample_count('Root', 'b') == 1.0


@pytest.mark.parametrize('tracker', [
    # old correctly tracks time for y1 if only low level is slow
    #  but does not track time for x1, x2 separately
    # GraphMetrics,
    # new correctly tracks time for x1, x2 separately but does not see y1 low level slowness, because y1 proc is just a simple return
    # of value from index
    GraphMetricsNew
])
def test_track_time(tracker, graph_name, sample_sum):

    x1 = 0.12  # 12 + 22 + 52 = 86, because all fields are from LL
                # 12 + 32 + 52 = 96
    x2 = 0.22 # 34
    x3 = 0.32 # 66 # HL only field
    y1 = 0.52 # 118, 1.18
    y2 = 0.62 # 180

    @listify
    def x_fields(fields, ids):
        """LL"""
        def get_field(f):
            if f == 'x1':
                return x1
            elif f == 'x2':
                return x2

        for id_ in ids:
            yield [get_field(f.name) for f in fields]

    @listify
    def y_fields(fields, ids):
        """LL"""
        def get_field(f):
            if f == 'y1':
                time.sleep(y1)
                return y1
            elif f == 'y2':
                return y2

        for id_ in ids:
            yield [get_field(f.name) for f in fields]

    def root_fields(fields):
        return [1 for _ in fields]

    def x_link():
        return 2

    ll_graph = Graph([
        Node('X', [
            Field('x1', None, x_fields),
            Field('x2', None, x_fields),
        ]),
        Node('Y', [
            Field('y1', None, y_fields),
            Field('y2', None, y_fields),
        ]),
    ])

    x_sg = SubGraph(ll_graph, 'X')
    y_sg = SubGraph(ll_graph, 'Y')

    @define(Any)
    def x1_field(val):
        """HL"""
        time.sleep(x1)
        return val

    @define(Any)
    def x2_field(val):
        """HL"""
        # time.sleep(x2)
        return val

    @listify
    def x3_field(fields, ids):
        """HL"""
        def get_field(f):
            if f == 'x3_3':
                # time.sleep(x3)
                return x3

        for id_ in ids:
            yield [get_field(f.name) for f in fields]

    @define(Any)
    def y2_field(val):
        """HL"""
        # time.sleep(y2)
        return val

    hl_graph = Graph([
        Node('X_h', [
            Field('x1_1', None, x_sg.c(x1_field(S.this.x1))),
            Field('x2_2', None, x_sg.c(x2_field(S.this.x2))),
            # in old tracker x3_3 is the only field that is tracked correctly
            #  because it not uses subgraph
            Field('x3_3', None, x3_field),
            Field('y1_1', None, y_sg.c(S.this.y1)),
            Field('y2_2', None, y_sg.c(y2_field(S.this.y2))),
        ]),
        Root([
            Field('a', None, root_fields),
            Link('x', TypeRef['X_h'], x_link, requires=None),
        ]),
    ])

    hl_graph = apply(hl_graph, [tracker(graph_name)])

    result = Engine(SyncExecutor()).execute(hl_graph, q.Node([
        # q.Field('a'),
        q.Link('x', q.Node([
            q.Field('x1_1'),
            q.Field('x2_2'),
            q.Field('x3_3'),
            q.Field('y1_1'),
            q.Field('y2_2'),
        ])),
    ]))
    # check_result(result, {
    #     'a': 1,
    #     'x': {
    #         'x1_1': x1,
    #         'x2_2': x2,
    #         'x3_3': x3,
    #         'y1_1': y1,
    #     },
    # })

    print('')
    print('Testing with', tracker.__name__)

    got_x = sum([
        sample_sum('X_h', 'x1_1'),
        sample_sum('X_h', 'x2_2'),
        sample_sum('X_h', 'x3_3'),
        sample_sum('X_h', 'y1_1'),
        sample_sum('X_h', 'y2_2')
    ])
    sample_sum('X_h', 'x1_1__define'),
    sample_sum('X_h', 'x2_2__define'),
    sample_sum('X_h', 'y1_1__define'),
    sample_sum('X_h', 'y2_2__define')
    print('x total exp', x1 + x2 + x3 + y1 + y2)
    print('x total got', got_x)
