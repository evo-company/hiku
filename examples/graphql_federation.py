import logging

from typing import (
    TypedDict,
    List,
    Any,
)

from flask import Flask, request, jsonify

from federation.entities import FederatedResolver
from federation.graph import (
    FederatedGraph,
    ExtendLink,
    ExtendNode,
)
from federation.util import HashableDict
from hiku.graph import Root, Field, Option
from hiku.types import (
    Integer,
    TypeRef,
    String,
    Sequence,
    Optional,
)
from hiku.engine import (
    Engine,
)
from hiku.executors.sync import SyncExecutor
from hiku.endpoint.graphql import GraphQLEndpoint


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


class AstronautResolver(FederatedResolver):
    def __call__(self, fields, ids):
        res = []

        for astro_id in ids:
            astronaut = astronauts.get(astro_id, default_astronaut)
            res.append([self._get_field(f, astronaut) for f in fields])

        return res

    def _get_field(self, f: Field, astronaut: Astronaut):
        if f.name == 'id':
            return astronaut['id']
        if f.name == 'name':
            return astronaut['name']
        if f.name == 'age':
            return astronaut['age']

    def resolve_references(
            self,
            refs: List[HashableDict],
            fields: List[Field]
    ) -> List[Any]:
        result = []
        for ref in refs:
            astronaut = astronauts.get(ref['id'], default_astronaut)
            result.append({
                f.name: self._get_field(f, astronaut) for f in fields
            })

        return result


def direct_link_id(opts):
    return opts['id']


def link_astronauts():
    return [1, 2]


astronaut_resolver = AstronautResolver()


QUERY_GRAPH = FederatedGraph([
    ExtendNode('Astronaut', [
        Field('id', Integer, astronaut_resolver),
        Field('name', String, astronaut_resolver),
        Field('age', Integer, astronaut_resolver),
    ], keys=['id']),
    Root([
        ExtendLink(
            'astronaut',
            Optional[TypeRef['Astronaut']],
            direct_link_id,
            requires=None,
            options=[
                Option('id', Integer)
            ],
        ),
        ExtendLink(
            'astronauts',
            Sequence[TypeRef['Astronaut']],
            link_astronauts,
            requires=None,
            options=None,
        ),
    ]),
])


app = Flask(__name__)

graphql_endpoint = GraphQLEndpoint(
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
