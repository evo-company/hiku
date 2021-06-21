from collections import defaultdict
from typing import List

from federation.graph import FederatedGraph
from hiku.engine import (
    InitOptions,
    Query,
    Context,
)
from hiku.executors.queue import Queue


class KeyNotFound(Exception):
    def __init__(self, key, rep):
        super().__init__(f'No key "{key}" in representation "{rep}"')


def get_keys(graph, typename) -> List[int]:
    node = graph.nodes_map[typename]
    return [
        d.args_map['fields'].value for d in
        filter(lambda d: d.name == 'key', node.directives)
    ]


class Engine:
    def __init__(self, executor):
        self.executor = executor

    def execute(self, graph: FederatedGraph, query, ctx=None):
        if ctx is None:
            ctx = {}

        if '_entities' in query.fields_map:
            entities_link = query.fields_map['_entities']
            query = entities_link.node

            queue = Queue(self.executor)
            task_set = queue.fork(None)
            query_workflow = Query(queue, task_set, graph, query, Context(ctx))

            representations = entities_link.options['representations']

            type_ids_map = defaultdict(list)

            for rep in representations:
                typename = rep['__typename']
                keys = get_keys(graph, typename)
                # TODO refactor [0], apollo has __resolveReference to pass ident as is
                key = keys[0]
                if key not in rep:
                    raise KeyNotFound(key, rep)
                ident = rep[key]

                type_ids_map[typename].append(ident)

            for typename in type_ids_map:
                ids = type_ids_map[typename]
                node = graph.nodes_map[typename]
                query_workflow.process_node(node, query, ids)
        else:
            query = InitOptions(graph).visit(query)
            queue = Queue(self.executor)
            task_set = queue.fork(None)
            query_workflow = Query(queue, task_set, graph, query, Context(ctx))

            query_workflow.start()

        res = self.executor.process(queue, query_workflow)
        return res
