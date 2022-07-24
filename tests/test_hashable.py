import pytest

from dataclasses import dataclass

from hiku.builder import build, Q
from hiku.engine import Engine, ResultTypeError
from hiku.executors.sync import SyncExecutor
from hiku.graph import Graph, Node, Field, Root, Link, Option
from hiku.types import (
    Any,
    Integer,
    TypeRef,
    String,
    Sequence,
)


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
            Link('user', TypeRef['user'],  link_user,  requires=None),
        ]),
    ])

    with pytest.raises(ResultTypeError) as err:
        execute(GRAPH, build([
            Q.user[
                Q.id,
                Q.info[
                    Q.age
                ]
            ]
        ]))
    err.match(
        "Link 'user.info' requires Field 'user._data' "
        "which contains unashable data:"
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
            Link('user', TypeRef['user'],  link_user,  requires=None),
        ]),
    ])

    with pytest.raises(ResultTypeError) as err:
        execute(GRAPH, build([
            Q.user[
                Q.id,
                Q.tags[Q.name]
            ]
        ]))
    # TODO this message does not make sense in this scenario
    err.match(
        "Link 'user.tags' requires Field 'user.id' "
        "which contains unashable data:"
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
            Link('user', TypeRef['user'],  link_user,  requires=None),
        ]),
    ])

    with pytest.raises(ResultTypeError) as err:
        execute(GRAPH, build([Q.user[Q.id]]))
    err.match(
        "Link 'Root.user' resolver 'link_user' returns unhashable object:"
    )


def test_root_link_requires_field_with_unhashable_data():
    @dataclass
    class User:
        id: int

    def user_data(fields):
        return [User(1)]

    def user_fields(fields, ids):
        ...

    GRAPH = Graph([
        Node('user', [
            Field('id', Integer, user_fields),
        ]),
        Root([
            Field('_user', Any,  user_data),
            Link('user', TypeRef['user'],  direct_link,  requires='_user'),
        ]),
    ])

    with pytest.raises(ResultTypeError) as err:
        execute(GRAPH, build([Q.user[Q.id]]))
    err.match(
        "Link 'Root.user' requires Field 'Root._user' "
        "which contains unashable data:"
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

    with pytest.raises(ResultTypeError) as err:
        execute(GRAPH, build([Q.user(id=1)[Q.id]]))
    err.match(
        "Link 'Root.user' resolver 'link_options' returns unhashable object:"
    )
