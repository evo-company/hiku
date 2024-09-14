import logging
from pathlib import Path

from flask import Flask, request, jsonify

from hiku.graph import Graph, Root, Field, Option
from hiku.types import Record, Integer, TypeRef, String, Boolean
from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.endpoint.graphql import GraphQLEndpoint


log = logging.getLogger(__name__)


def value_func(fields):
    return ["Hello World!" for _ in fields]


def action_func(fields):
    results = []
    for field in fields:
        print("action performed!", field.options)
        results.append(True)
    return results


DATA_TYPES = {
    "Point": Record[
        {
            "x": Integer,
            "y": Integer,
        }
    ],
    "Data": Record[
        {
            "point": TypeRef["Point"],
        }
    ],
}

QUERY_GRAPH = Graph(
    [
        Root(
            [
                Field("value", String, value_func),
            ]
        ),
    ],
    data_types=DATA_TYPES,
)

MUTATION_GRAPH = Graph(
    QUERY_GRAPH.nodes
    + [
        Root(
            [
                Field(
                    "action",
                    Boolean,
                    action_func,
                    options=[Option("data", TypeRef["Data"])],
                ),
            ]
        ),
    ],
    data_types=DATA_TYPES,
)


app = Flask(__name__)

graphql_endpoint = GraphQLEndpoint(
    Engine(SyncExecutor()),
    QUERY_GRAPH,
    MUTATION_GRAPH,
)


@app.route("/graphql", methods={"POST"})
def handle_graphql():
    data = request.get_json()
    result = graphql_endpoint.dispatch(data)
    return jsonify(result)


@app.route("/", methods={"GET"})
def graphiql():
    path = Path(__file__).parent / "graphiql.html"
    with open(path) as f:
        return f.read().encode("utf-8")


def main():
    logging.basicConfig()
    log.setLevel(logging.INFO)
    log.info("GraphiQL is available on http://localhost:5000")
    log.info("GraphQL endpoint is running on http://localhost:5000/graphql")
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
