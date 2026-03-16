import typing
from dataclasses import dataclass

from hiku.engine import pass_context
from hiku.graph import Field, Graph, Node, Root
from hiku.sources import sqlalchemy
from hiku.types import Integer, String, Record
from hiku.expr.core import define

human_query = sqlalchemy.FieldsQuery(
    "db.session_images_async",
    ...,  # type: ignore
)

db_graph = Graph(
    [
        Node(
            "human",
            [
                Field("id", Integer, human_query),
                Field("name", String, human_query),
                Field("quotes", None, human_query),
                Field("image_id", None, human_query),
                Field("droid_ids", None, human_query),
            ],
        ),
    ]
)


@pass_context
def map_low_level_context(context: dict, fields: list) -> list[typing.Any]:
    def get_field(fname: str) -> typing.Any:
        if fname == "some_context":
            return context["some_context"]
        return None

    return [get_field(f.name) for f in fields]


low_level_graph = Graph(
    db_graph.items
    + [Root([Field("some_context", String, map_low_level_context)])]
)


@dataclass
class DroidCtx:
    id: int
    name: str


@dataclass
class HumanStatusCtx:
    value: str
    title: str


PARTNERS = {
    1: 2,
    3: 4,
}

SPACESHIP_IDS = {
    1: 1234,
    2: 5678,
}


@define(Record[{"name": String}])
def get_full_name(p: typing.Any) -> str:
    return p.name


@define(Integer)
def get_droid_labels(id: int) -> list[str]:
    return []


@define(Record[{"id": Integer, "name": String}])
def get_human_status_def(human: typing.Any) -> HumanStatusCtx:
    return HumanStatusCtx(value="active", title="Heyo")


@define(Integer, String)
def get_episodes(id: int, some_context: str) -> list[dict]:
    return [
        {
            "no": no,
            "name": some_context[no:],
        }
        for no in range(6)
        if id % no == 0
    ]
