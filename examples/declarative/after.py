import typing
from dataclasses import dataclass

from hiku.directives import Deprecated
from hiku.expr.core import S
from hiku.sources.graph import SubGraph

import hiku.declarative.graph as hiku

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


def link_partner(ids: list[int], ctx: dict) -> list[hiku.link["Human"]]:
    return [hiku.link.from_(PARTNERS.get(i, 0)) for i in ids]


def get_spaceship_id(ids: list[int], ctx: dict) -> list[int]:
    return [SPACESHIP_IDS[i] for i in ids]


@hiku.options
class DroidOpts:
    is_ok: bool = hiku.opt(default=False, name="is_ok", description="ok")


def link_droids(
    labels_lists: list[list[str]],
    ctx: dict,
    opts: DroidOpts,
) -> list[list[hiku.link["Droid"]]]:
    if opts.is_ok:
        print("is_okk")
    return [
        [hiku.link.from_(DroidCtx(id=1, name=i)) for i in labels]
        for labels in labels_lists
    ]


def get_serial_number(objs: list[DroidCtx], ctx: dict) -> list[str]:
    return [f"{obj.id}-{obj.name}" for obj in objs]


@hiku.options
class ImageOpts:
    width: int
    height: int


def get_image(ps: list, ctx: dict, opts: ImageOpts) -> list[str | None]:
    return [f"{p.image}x{opts.width}x{opts.height}" for p in ps]


@dataclass
class EpisodeCtx:
    no: int
    name: str


@hiku.options
class EpisodesOpts:
    timestamp: int | None = hiku.opt(default=None)


def map_episodes(
    dict_lists: list[list[dict]],
    ctx: dict,
    opts: EpisodesOpts,
) -> list[list[hiku.link["Episode"]]]:
    return [
        [hiku.link.from_(EpisodeCtx(no=d["no"], name=d["name"])) for d in dicts]
        for dicts in dict_lists
    ]


@hiku.node
class HumanStatus:
    __key__: "HumanStatus"

    value: str = hiku.field(description="one of: ['active', 'deceased', '??']")
    title: str


@hiku.node
class Droid:
    __key__: DroidCtx

    id: int
    name: str
    serial_number: str = hiku.field(get_serial_number, name="serialNo")


@hiku.node
class Episode:
    __key__: EpisodeCtx

    no: int
    name: str


@hiku.node
class Human:
    __key__: int

    id: int = hiku.field(preresolve=human_sg)
    full_name: str = hiku.field(preresolve=human_sg.c(get_full_name(S.this)))
    quotes: list[str] = hiku.field(preresolve=human_sg.c(S.this.quotes))
    image: str | None = hiku.field(
        get_image,
        preresolve=human_sg.c(S.this.image_id),
        options=ImageOpts,
    )
    spaceship_id: int | None = hiku.field(get_spaceship_id)
    legacy_field: bool = hiku.field(
        lambda objs, ctx: [True] * len(objs),
        directives=[Deprecated("this field is so old")],
        name="legacy_field",
    )
    episodes: list[hiku.link[Episode]] = hiku.field(
        map_episodes,
        preresolve=human_sg.c(get_episodes(S.this.id, S.some_context)),
        options=EpisodesOpts,
    )
    status: hiku.link[HumanStatus] = hiku.field(
        preresolve=human_sg.c(get_human_status_def(S.this)),
    )
    droids: list[hiku.link[Droid]] = hiku.field(
        resolve=link_droids,
        preresolve=human_sg.c(get_droid_labels(S.this.id)),
        options=DroidOpts,
    )
    partner: hiku.link["Human"] = hiku.field(link_partner)
