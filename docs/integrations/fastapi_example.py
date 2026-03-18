import uvicorn
from fastapi import FastAPI, Request

from hiku.types import  String
from hiku.graph import Graph, Root, Field
from hiku.engine import Engine
from hiku.endpoint.graphql import AsyncGraphQLEndpoint
from hiku.executors.asyncio import AsyncIOExecutor

def say_hello(fields):
    return ['Hello World!' for _ in fields]

QUERY_GRAPH = Graph([
    Root([Field('hello', String, say_hello)]),
])

app = FastAPI()

graphql_endpoint = AsyncGraphQLEndpoint(
    Engine(AsyncIOExecutor()), QUERY_GRAPH
)
redis = Redis()

@app.post('/graphql')
async def handle_graphql(request: Request):
    data = await request.json()
    context = {
        'redis': redis,
    }
    return await graphql_endpoint.dispatch(data, context)


if __name__ == "__main__":
    uvicorn.run(__name__ + ":app", port=5000, host="0.0.0.0")
