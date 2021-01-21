from collections import defaultdict

from federation.graph import FederatedGraph
from hiku.engine import (
    InitOptions,
    Query,
    Context,
)
from hiku.executors.queue import Queue


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
                keys = graph.extend_node_keys_map[typename]
                # TODO refactor [0], apollo has __resolveReference to pass ident as is
                key = keys[0]
                ident = rep[key]

                type_ids_map[typename].append(ident)

            # TODO hiku federation can support multiple __typename in one query
            #  but I do not know if its required
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
