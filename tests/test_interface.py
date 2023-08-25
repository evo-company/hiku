import pytest
from hiku.denormalize.graphql import DenormalizeGraphQL

from hiku.endpoint.graphql import GraphQLEndpoint
from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.graph import Field, Graph, Interface, Link, Node, Option, Root
from hiku.types import Integer, InterfaceRef, Optional, Sequence, String, TypeRef
from hiku.utils import empty_field, listify
from hiku.readers.graphql import read
from hiku.validate.graph import GraphValidationError
from hiku.validate.query import validate


def execute(graph, query):
    engine = Engine(SyncExecutor())
    result = engine.execute(query, graph)
    return DenormalizeGraphQL(graph, result, "query").process(query)


@listify
def resolve_user_fields(fields, ids):
    def get_field(fname, id_):
        if fname == 'id':
            return id_

    for id_ in ids:
        yield [get_field(f.name, id_) for f in fields]


@listify
def resolve_audio_fields(fields, ids):
    def get_field(fname, id_):
        if fname == 'id':
            return id_
        if fname == 'duration':
            return f'{id_}s'
        if fname == 'album':
            return f'album#{id_}'

    for id_ in ids:
        yield [get_field(f.name, id_) for f in fields]


@listify
def resolve_video_fields(fields, ids):
    def get_field(fname, id_):
        if fname == 'id':
            return id_
        if fname == 'duration':
            return f'{id_}s'
        if fname == 'thumbnailUrl':
            return f'/video/{id_}'

    for id_ in ids:
        yield [get_field(f.name, id_) for f in fields]


def link_user_media():
    return [
        (1, TypeRef['Audio']),
        (2, TypeRef['Video']),
    ]


def link_user():
    return 111


def search_media(opts):
    if opts['text'] != 'foo':
        return []
    return [
        (1, TypeRef['Audio']),
        (2, TypeRef['Video']),
        (3, TypeRef['Audio']),
        (4, TypeRef['Video']),
    ]


def get_media():
    return 1, TypeRef['Audio']


def maybe_get_media():
    return 2, TypeRef['Video']


GRAPH = Graph([
    Node('Audio', [
        Field('id', Integer, resolve_audio_fields),
        Field('duration', String, resolve_audio_fields),
        Field('album', String, resolve_audio_fields),
    ], implements=['Media']),
    Node('Video', [
        Field('id', Integer, resolve_video_fields),
        Field('duration', String, resolve_video_fields),
        Field('thumbnailUrl', String, resolve_video_fields, options=[
            Option('size', Integer),
        ]),
    ], implements=['Media']),
    Node('User', [
        Field('id', Integer, resolve_user_fields),
        Link('media', Sequence[InterfaceRef['Media']], link_user_media, requires=None),
    ]),
    Root([
        Link(
            'searchMedia',
            Sequence[InterfaceRef['Media']],
            search_media,
            options=[
                Option('text', String),
            ],
            requires=None
        ),
        Link('media', InterfaceRef['Media'], get_media, requires=None),
        Link('maybeMedia', Optional[InterfaceRef['Media']], maybe_get_media, requires=None),
        Link('user', Optional[TypeRef['User']], link_user, requires=None),
    ]),
], interfaces=[
    Interface('Media', [
        Field('id', Integer, empty_field),
        Field('duration', String, empty_field),
    ]),
])


def test_validate_graph_with_interface():
    with pytest.raises(GraphValidationError) as err:
        Graph([
            Node('Audio', [
                Field('id', Integer, resolve_audio_fields),
                Field('duration', String, resolve_audio_fields),
                Field('album', String, resolve_audio_fields),
            ], implements=['WrongInterface']),
            Node('Video', [
                Field('id', Integer, resolve_video_fields),
                Field('duration', String, resolve_video_fields),
                Field('thumbnailUrl', String, resolve_video_fields),
            ], implements=['Media']),
            Root([
                Link(
                    'searchMedia',
                    Sequence[InterfaceRef['Media']],
                    search_media,
                    options=[
                        Option('text', String),
                    ],
                    requires=None
                ),
            ]),
        ], interfaces=[
            Interface('Media', []),
            Interface('', [Field('id', Integer, empty_field)]),
            Interface('Invalid', ['WrongType']),  # type: ignore
        ])

    assert err.value.errors == [
        'Node "Audio" implements missing interface "WrongInterface"',
        "Interface 'Media' must have at least one field",
        'Interface must have a name',
        "Interface 'Invalid' fields must be of type 'Field', found '['WrongType']'",
    ]


def test_option_not_provided_for_field():
    query = """
    query GetMedia {
      media {
        __typename
        id
        duration
        ... on Audio {
          album
        }
        ... on Video {
          thumbnailUrl
        }
      }
    }
    """
    with pytest.raises(TypeError) as err:
        execute(GRAPH, read(query))
        err.match("Required option \"size\" for Field('thumbnailUrl'")


def test_root_link_to_interface_list():
    query = """
    query SearchMedia($text: String) {
      searchMedia(text: $text) {
        __typename
        id
        duration
        ... on Audio {
          album
        }
        ... on Video {
          thumbnailUrl(size: 100)
        }
      }
    }
    """

    result = execute(GRAPH, read(query, {'text': 'foo'}))
    assert result == {
        'searchMedia': [
            {'__typename': 'Audio', 'id': 1, 'duration': '1s', 'album': 'album#1'},
            {'__typename': 'Video', 'id': 2, 'duration': '2s', 'thumbnailUrl': '/video/2'},
            {'__typename': 'Audio', 'id': 3, 'duration': '3s', 'album': 'album#3'},
            {'__typename': 'Video', 'id': 4, 'duration': '4s', 'thumbnailUrl': '/video/4'},
        ]
    }


def test_root_link_to_interface_one():
    query = """
    query GetMedia {
      media {
        __typename
        id
        duration
        ... on Audio {
          album
        }
        ... on Video {
          thumbnailUrl(size: 100)
        }
      }
    }
    """
    result = execute(GRAPH, read(query))
    assert result == {
        'media': {'__typename': 'Audio', 'id': 1, 'duration': '1s', 'album': 'album#1'},
    }


def test_root_link_to_interface_optional():
    query = """
    query MaybeGetMedia {
      maybeMedia {
        __typename
        id
        duration
        ... on Audio {
          album
        }
        ... on Video {
          thumbnailUrl(size: 100)
        }
      }
    }
    """
    result = execute(GRAPH, read(query))
    assert result == {
        'maybeMedia': {'__typename': 'Video', 'id': 2, 'duration': '2s', 'thumbnailUrl': '/video/2'},
    }


def test_non_root_link_to_interface_list():
    query = """
    query GetUserMedia {
      user {
        id
        media {
          __typename
          id
          duration
          ... on Audio {
            album
          }
          ... on Video {
            thumbnailUrl(size: 100)
          }
        }
      }
    }
    """
    result = execute(GRAPH, read(query))
    assert result == {
        'user': {
            'id': 111,
            'media': [
                {'__typename': 'Audio', 'id': 1, 'duration': '1s', 'album': 'album#1'},
                {'__typename': 'Video', 'id': 2, 'duration': '2s', 'thumbnailUrl': '/video/2'},
            ]
        }
    }


def test_query_with_inline_fragment_and_fragment_spread():
    query = """
    query GetMedia {
      media {
        __typename
        id
        duration
        ...AudioFragment
        ... on Video {
          thumbnailUrl(size: 100)
        }
      }
    }
    
    fragment AudioFragment on Audio {
        album
    }
    """
    result = execute(GRAPH, read(query))
    assert result == {
        'media': {'__typename': 'Audio', 'id': 1, 'duration': '1s', 'album': 'album#1'},
    }


def test_query_can_be_without_shared_fields():
    query = """
    query GetMedia {
      media {
        __typename
        ... on Audio {
          id
          duration
          album
        }
        ... on Video {
          id
          duration
          thumbnailUrl(size: 100)
        }
      }
    }
    """

    result = execute(GRAPH, read(query))
    assert result == {
        'media': {'__typename': 'Audio', 'id': 1, 'duration': '1s', 'album': 'album#1'},
    }


def test_query_only_one_interface_type():
    query = """
    query GetMedia {
      media {
        __typename
        id
        duration
        ... on Audio {
          album
        }
      }
    }
    """

    result = execute(GRAPH, read(query))
    assert result == {
        'media': {'__typename': 'Audio', 'id': 1, 'duration': '1s', 'album': 'album#1'},
    }


def test_query_only_shared_fields():
    query = """
    query GetMedia {
      media {
        __typename
        id
        duration
      }
    }
    """

    result = execute(GRAPH, read(query))
    assert result == {
        'media': {'__typename': 'Audio', 'id': 1, 'duration': '1s'},
    }


def test_validate_interface_has_no_implementations():
    graph = Graph([
        Root([
            Link(
                'media',
                InterfaceRef['Media'],
                lambda: None,
                requires=None
            ),
        ]),
    ], interfaces=[
        Interface('Media', [
            Field('id', Integer, empty_field),
            Field('duration', String, empty_field),
        ]),
    ])

    query = """
    query GetMedia {
      media {
        id
        duration
      }
    }
    """

    errors = validate(graph, read(query))

    assert errors == [
        "Can not query field 'id' on interface 'Media'. "
        "Interface 'Media' is not implemented by any type. "
        "Add at least one type implementing this interface.",

        "Can not query field 'duration' on interface 'Media'. Interface 'Media' "
        "is not implemented by any type. Add at least one type implementing this "
        "interface.",
    ]


def test_validate_query_implementation_node_field_without_inline_fragment():
    query = """
    query GetMedia {
      media {
        id
        duration
        album
      }
    }
    """

    errors = validate(GRAPH, read(query))

    assert errors == [
        "Can not query field 'album' on type 'Media'. "
        "Did you mean to use an inline fragment on 'Audio'?"
    ]


def test_validate_interface_type_has_no_such_field():
    query = """
    query SearchMedia($text: String) {
      searchMedia(text: $text) {
        ... on Audio {
          invalid_field
          duration
        }
        ... on Video {
          thumbnailUrl(size: 100)
        }
      }
    }
    """

    errors = validate(GRAPH, read(query, {'text': 'foo'}))

    assert errors == [
        'Field "invalid_field" is not implemented in the "Audio" node',
    ]


def test_validate_interface_type_field_has_no_such_option():
    query = """
    query SearchMedia($text: String) {
      searchMedia(text: $text) {
        ... on Audio {
          duration(size: 100)
        }
        ... on Video {
          thumbnailUrl(size: 100)
        }
      }
    }
    """

    errors = validate(GRAPH, read(query, {'text': 'foo'}))

    assert errors == [
        'Unknown options for "Audio.duration": size',
    ]
