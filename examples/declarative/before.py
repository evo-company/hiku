import typing

import hiku.query
from hiku.directives import Deprecated
from hiku.expr.core import S, define
from hiku.graph import Field, Link, Node, Option
from hiku.sources.graph import SubGraph
from hiku.types import (
    Any,
    Boolean,
    Integer,
    Optional,
    Record,
    Sequence,
    String,
    TypeRef,
)

from .common import (
    PARTNERS,
    SPACESHIP_IDS,
    DroidCtx,
    get_droid_labels,
    get_episodes,
    get_full_name,
    get_human_status_def,
    low_level_graph,
)

human_sg: typing.Any = SubGraph(low_level_graph, "human")


def link_partner(ids: list[int]) -> list[int]:
    return [PARTNERS.get(i, 0) for i in ids]


def direct_link(ids: list) -> list:
    return ids


def get_spaceship_id(_fields: list, ids: list[int]) -> list[list[int]]:
    return [[SPACESHIP_IDS[i]] for i in ids]


def link_droids(
    labels_lists: list[list[str]],
    opts: dict,
) -> list[list[DroidCtx]]:
    if opts["is_ok"]:
        print("is_okk")
    return [[DroidCtx(id=1, name=i) for i in labels] for labels in labels_lists]


def map_droid(
    fields: list[hiku.query.Field], objs: list[DroidCtx]
) -> list[list[typing.Any]]:
    def get_field(f_name: str, obj: DroidCtx) -> typing.Any:
        if f_name == "serialNo":
            return f"{obj.id}-{obj.name}"
        return getattr(obj, f_name)

    return [[get_field(f.name, obj) for f in fields] for obj in objs]


@define(Integer, Integer, Integer)
def get_image_def(image_id: int, width: int, height: int) -> str:
    return f"{image_id}x{width}x{height}"


def get_tuple_fields(
    fields: list[hiku.query.Field], tuples: list
) -> list[list]:
    return [[getattr(t, f.name) for f in fields] for t in tuples]


HumanStatusNode = Node(
    "HumanStatus",
    [
        Field(
            "value",
            String,
            get_tuple_fields,
            description="one of: ['active', 'deceased', '??']",
        ),
        Field("title", String, get_tuple_fields),
    ],
)

DroidNode = Node(
    "Droid",
    [
        Field("id", Integer, map_droid),
        Field("name", String, map_droid),
        Field("serialNo", String, map_droid),
    ],
)

EpisodeRecord = Record[
    {
        "no": Integer,
        "name": String,
    }
]


HumanNode = Node(
    "Human",
    [
        #
        Field("id", Integer, human_sg),
        Field("fullName", String, human_sg.c(get_full_name(S.this))),
        Field("quotes", Sequence[String], human_sg.c(S.this.quotes)),
        Field(
            "image",
            Optional[String],
            human_sg.c(get_image_def(S.this.image_id, S.width, S.height)),
            options=[
                Option("width", Integer),
                Option("height", Integer),
            ],
        ),
        Field("spaceshipId", Optional[Integer], get_spaceship_id),
        Field(
            "legacy_field",
            Boolean,
            lambda f, objs: [[True]] * len(objs),
            directives=[Deprecated("this field is very old")],
        ),
        Field(
            "episodes",
            Sequence[TypeRef["Episode"]],
            human_sg.c(get_episodes(S.this.id, S.some_context)),
            options=[Option("timestamp", Optional[Integer], default=None)],
        ),
        Field("_status", Any, human_sg.c(get_human_status_def(S.this))),
        Link(
            "status",
            TypeRef["HumanStatus"],
            direct_link,
            requires="_status",
        ),
        Field(
            "_droid_labels",
            Any,
            human_sg.c(get_droid_labels(S.this.id)),
        ),
        Link(
            "droids",
            Sequence[TypeRef["Droid"]],
            link_droids,
            requires="_droid_labels",
            options=[Option("is_ok", Boolean, default=False, description="ok")],
        ),
        Link(
            "partner",
            Optional[TypeRef["Human"]],
            link_partner,
            requires="id",
        ),
    ],
)
