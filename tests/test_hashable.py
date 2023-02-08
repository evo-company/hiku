import pytest

from typing import List
from dataclasses import dataclass

from hiku.builder import build, Q
from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.graph import Graph, Node, Field, Root, Link, Option
from hiku.types import (
    Any,
    Integer,
    TypeRef,
    String,
    Sequence,
)
from hiku.utils import listify


def direct_link(ids):
    return ids


def execute(graph, query_, ctx=None):
    engine = Engine(SyncExecutor())
    return engine.execute(graph, query_, ctx=ctx)


def test_link_requires_field_with_unhashable_data():
    @dataclass(frozen=True)
    class User:
        id: int

    @dataclass
    class UserData:
        age: int

    def link_user():
        return User(1)

    def user_info_fields(fields, data):
        return [
            [getattr(d, f.name) for f in fields]
            for d in data
        ]

    def user_fields(fields, ids):
        def map_field(f, user):
            if f.name == 'id':
                return user.id
            if f.name == '_data':
                return UserData(20)

        return [[map_field(f, user) for f in fields] for user in ids]

    GRAPH = Graph([
        Node('userInfo', [
            Field('age', Integer, user_info_fields),
        ]),
        Node('user', [
            Field('id', Integer, user_fields),
            Field('_data', Any, user_fields),
            Link('info', TypeRef['userInfo'], direct_link, requires='_data'),
        ]),
        Root([
            Link('user', TypeRef['user'], link_user, requires=None),
        ]),
    ])

    with pytest.raises(TypeError) as err:
        execute(GRAPH, build([
            Q.user[
                Q.id,
                Q.info[
                    Q.age
                ]
            ]
        ]))

    err.match(
        r"Can't store link values, node: 'user', link: 'info', "
        r"expected: list of hashable objects, returned:(.*UserData)"
    )


def test_link_to_sequence():
    @dataclass(frozen=True)
    class User:
        id: int

    @dataclass
    class Tag:
        name: str

    def link_user():
        return User(1)

    def tags_fields(fields, data):
        return [[getattr(d, f.name) for f in fields] for d in data]

    def user_fields(fields, users):
        return [[getattr(user, f.name) for f in fields] for user in users]

    def link_tags(ids):
        return [[Tag('tag1')] for id_ in ids]

    GRAPH = Graph([
        Node('tags', [
            Field('name', String, tags_fields),
        ]),
        Node('user', [
            Field('id', Integer, user_fields),
            Link('tags', Sequence[TypeRef['tags']], link_tags, requires='id'),
        ]),
        Root([
            Link('user', TypeRef['user'], link_user, requires=None),
        ]),
    ])

    with pytest.raises(TypeError) as err:
        execute(GRAPH, build([
            Q.user[
                Q.id,
                Q.tags[Q.name]
            ]
        ]))

    err.match(
        r"Can't store link values, node: 'user', link: 'tags', "
        r"expected: list \(len: 1\) of lists of hashable objects, "
        r"returned:(.*Tag)"
    )


def test_root_link_resolver_returns_unhashable_data():
    @dataclass
    class User:
        id: int

    def link_user():
        return User(1)

    def user_fields(fields, ids):
        def map_field(f, user):
            if f.name == 'id':
                return user.id

        return [[map_field(f, user) for f in fields] for user in ids]

    GRAPH = Graph([
        Node('user', [
            Field('id', Integer, user_fields),
        ]),
        Root([
            Link('user', TypeRef['user'], link_user, requires=None),
        ]),
    ])

    with pytest.raises(TypeError) as err:
        execute(GRAPH, build([Q.user[Q.id]]))

    err.match(
        r"Can't store link values, node: '__root__', link: 'user', "
        r"expected: hashable object, returned:(.*User)"
    )


def test_root_link_requires_field_with_unhashable_data():
    @dataclass
    class User:
        id: int

    def user_data(fields):
        return [User(1)]

    @listify
    def user_fields(fields, ids):
        for id_ in ids:
            yield [getattr(id_, f.name) for f in fields]

    GRAPH = Graph([
        Node('user', [
            Field('id', Integer, user_fields),
        ]),
        Root([
            Field('_user', Any, user_data),
            Link('user', TypeRef['user'], direct_link, requires='_user'),
        ]),
    ])

    with pytest.raises(TypeError) as err:
        execute(GRAPH, build([Q.user[Q.id]]))

    err.match(
        r"Can't store link values, node: '__root__', link: 'user', "
        r"expected: hashable object, returned:(.*User)"
    )


def test_root_link_options_unhashable_data():
    @dataclass
    class UserOpts:
        id: int

    def user_fields(fields, ids):
        ...

    def link_options(opts):
        return UserOpts(opts['id'])

    GRAPH = Graph([
        Node('user', [
            Field('id', Integer, user_fields),
        ]),
        Root([
            Link(
                'user',
                TypeRef['user'],
                link_options,
                requires=None,
                options=[Option('id', Integer)]
            ),
        ]),
    ])

    with pytest.raises(TypeError) as err:
        execute(GRAPH, build([Q.user(id=1)[Q.id]]))

    err.match(
        r"Can't store link values, node: '__root__', link: 'user', "
        r"expected: hashable object, returned:(.*User)"
    )


@pytest.mark.parametrize('typ, expected', [
    (list, 'list'),
    (set, 'set'),
])
def test_hint_unhashble_type(typ, expected):
    GRAPH = Graph([
        Node('user', [
            Field('tags', Sequence[String], lambda fields, ids: None),
        ]),
        Root([
            Link(
                'user',
                TypeRef['user'],
                lambda: typ(['tag1']),
                requires=None,
            ),
        ]),
    ])

    with pytest.raises(TypeError) as err:
        execute(GRAPH, build([Q.user[Q.tags]]))

    err.match(f"Hint: Consider using tuple instead of '{expected}'.")


def test_hint_unhashble_type_in_tuple():
    GRAPH = Graph([
        Node('user', [
            Field('tags', Sequence[String], lambda fields, ids: [[]]),
        ]),
        Root([
            Link(
                'user',
                TypeRef['user'],
                lambda: tuple([{}, {}]),
                requires=None,
            ),
        ]),
    ])

    with pytest.raises(TypeError) as err:
        execute(GRAPH, build([Q.user[Q.tags]]))

    err.match(
        "Hint: Consider adding __hash__ method or use hashable type for '{}'.")


def test_hint_frozen_dataclass():
    @dataclass
    class User:
        tags: List[str]

    GRAPH = Graph([
        Node('user', [
            Field('tags', Sequence[String], lambda fields, ids: None),
        ]),
        Root([
            Link(
                'user',
                TypeRef['user'],
                lambda: User(['tag1']),
                requires=None,
            ),
        ]),
    ])

    with pytest.raises(TypeError) as err:
        execute(GRAPH, build([Q.user[Q.tags]]))

    err.match("Hint: Use @dataclass\\(frozen=True\\) on 'User'.")


def test_hint_dataclass_unhashable_field():
    @dataclass(frozen=True)
    class User:
        tags: List[str]

    GRAPH = Graph([
        Node('user', [
            Field('tags', Sequence[String], lambda fields, ids: None),
        ]),
        Root([
            Link(
                'user',
                TypeRef['user'],
                lambda: User(['tag1']),
                requires=None,
            ),
        ]),
    ])

    with pytest.raises(TypeError) as err:
        execute(GRAPH, build([Q.user[Q.tags]]))

    err.match("Hint: Field 'User.tags' of type 'list' is not hashable.")
