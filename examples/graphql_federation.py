import logging

from typing import (
    TypedDict,
)

from flask import Flask, request, jsonify

from federation.directive import KeyDirective
from federation.endpoint import FederatedGraphQLEndpoint
from federation.engine import Engine
from federation.graph import (
    FederatedGraph,
)
from hiku.graph import (
    Root,
    Field,
    Option,
    Node,
    Link,
)
from hiku.types import (
    Integer,
    TypeRef,
    String,
    Sequence,
    Optional,
)
from hiku.executors.sync import SyncExecutor

log = logging.getLogger(__name__)


class Astronaut(TypedDict):
    id: int
    name: str
    age: int


default_astronaut = Astronaut(id=99, name='Default Astro', age=99)
astronauts = {
    1: Astronaut(id=1, name='Max', age=20),
    2: Astronaut(id=2, name='Bob', age=25),
}


def astronaut_resolver(fields, ids):
    def _get_field(f: Field, astronaut: Astronaut):
        if f.name == 'id':
            return astronaut['id']
        if f.name == 'name':
            return astronaut['name']
        if f.name == 'age':
            return astronaut['age']

    res = []

    for astro_id in ids:
        astronaut = astronauts.get(astro_id, default_astronaut)
        res.append([_get_field(f, astronaut) for f in fields])

    return res


def direct_link_id(opts):
    return opts['id']


def link_astronauts():
    return [1, 2]


QUERY_GRAPH = FederatedGraph([
   Node('Astronaut', [
        Field('id', Integer, astronaut_resolver),
        Field('name', String, astronaut_resolver),
        Field('age', Integer, astronaut_resolver),
    ], directives=[KeyDirective('id')]),
    Root([
        Link(
            'astronaut',
            Optional[TypeRef['Astronaut']],
            direct_link_id,
            requires=None,
            options=[
                Option('id', Integer)
            ],
        ),
        Link(
            'astronauts',
            Sequence[TypeRef['Astronaut']],
            link_astronauts,
            requires=None,
            options=None,
        ),
    ]),
])


app = Flask(__name__)

graphql_endpoint = FederatedGraphQLEndpoint(
    Engine(SyncExecutor()),
    QUERY_GRAPH,
    # TODO Mutations
)


@app.route('/graphql', methods={'POST', 'OPTIONS'})
def handle_graphql():
    data = request.get_json()
    result = graphql_endpoint.dispatch(data)
    resp = jsonify(result)
    return resp


def main():
    logging.basicConfig()
    app.run(port=5000)


if __name__ == '__main__':
    main()
