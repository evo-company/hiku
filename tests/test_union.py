import pytest
from hiku.denormalize.graphql import DenormalizeGraphQL

from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.graph import Field, Graph, Link, Node, Option, Root, Union
from hiku.types import Integer, Optional, Sequence, String, TypeRef, UnionRef
from hiku.utils import listify
from hiku.readers.graphql import read
from hiku.validate.graph import GraphValidationError
from hiku.validate.query import validate


def execute(graph, query):
    engine = Engine(SyncExecutor())
    result = engine.execute(graph, query)
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

    for id_ in ids:
        yield [get_field(f.name, id_) for f in fields]


@listify
def resolve_video_fields(fields, ids):
    def get_field(fname, id_):
        if fname == 'id':
            return id_
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
        Link('user', TypeRef['User'], link_user, requires=None),
    ]),
    Node('Video', [
        Field('id', Integer, resolve_video_fields),
        Field('thumbnailUrl', String, resolve_video_fields, options=[
            Option('size', Integer),
        ]),
    ]),
    Node('User', [
        Field('id', Integer, resolve_user_fields),
        Link('media', Sequence[UnionRef['Media']], link_user_media, requires=None),
    ]),
    Root([
        Link(
            'searchMedia',
            Sequence[UnionRef['Media']],
            search_media,
            options=[
                Option('text', String),
            ],
            requires=None
        ),
        Link('media', UnionRef['Media'], get_media, requires=None),
        Link('maybeMedia', Optional[UnionRef['Media']], maybe_get_media, requires=None),
        Link('user', Optional[TypeRef['User']], link_user, requires=None),
    ]),
], unions=[
    Union('Media', ['Audio', 'Video']),
])


def test_validate_graph_union():
    with pytest.raises(GraphValidationError) as err:
        Graph([
            Node('Audio', [
                Field('id', Integer, resolve_audio_fields),
                Field('duration', String, resolve_audio_fields),
            ]),
            Node('Video', [
                Field('id', Integer, resolve_video_fields),
                Field('thumbnailUrl', String, resolve_video_fields),
            ]),
            Root([
                Link(
                    'searchMedia',
                    Sequence[UnionRef['Media']],
                    search_media,
                    options=[
                        Option('text', String),
                    ],
                    requires=None
                ),
            ]),
        ], unions=[
            Union('Media', []),
            Union('', ['Audio', 'Video']),
            Union('Invalid', ['Unknown']),
        ])

    assert err.value.errors == [
        'Union must have at least one type',
        'Union must have a name',
        "Union 'Invalid' types '['Unknown']' must point to node or data type",
    ]


def test_option_not_provided_for_field():
    query = """
    query GetMedia {
      media {
        __typename
        ... on Audio {
          id
          duration
        }
        ... on Video {
          id
          thumbnailUrl
        }
      }
    }
    """
    with pytest.raises(TypeError) as err:
        execute(GRAPH, read(query))
        err.match("Required option \"size\" for Field('thumbnailUrl'")


def test_root_link_to_union_list():
    query = """
    query SearchMedia($text: String) {
      searchMedia(text: $text) {
        __typename
        ... on Audio {
          id
          duration
        }
        ... on Video {
          id
          thumbnailUrl(size: 100)
        }
      }
    }
    """
    result = execute(GRAPH, read(query, {'text': 'foo'}))
    assert result == {
        'searchMedia': [
            {'__typename': 'Audio', 'id': 1, 'duration': '1s'},
            {'__typename': 'Video', 'id': 2, 'thumbnailUrl': '/video/2'},
            {'__typename': 'Audio', 'id': 3, 'duration': '3s'},
            {'__typename': 'Video', 'id': 4, 'thumbnailUrl': '/video/4'},
        ]
    }


def test_root_link_to_union_one():
    query = """
    query GetMedia {
      media {
        __typename
        ... on Audio {
          id
          duration
        }
        ... on Video {
          id
          thumbnailUrl(size: 100)
        }
      }
    }
    """
    result = execute(GRAPH, read(query))
    assert result == {
        'media': {'__typename': 'Audio', 'id': 1, 'duration': '1s'},
    }


def test_root_link_to_union_optional():
    query = """
    query MaybeGetMedia {
      maybeMedia {
        __typename
        ... on Audio {
          duration
        }
        ... on Video {
          thumbnailUrl(size: 100)
        }
      }
    }
    """
    result = execute(GRAPH, read(query))
    assert result == {
        'maybeMedia': {'__typename': 'Video', 'thumbnailUrl': '/video/2'},
    }


def test_non_root_link_to_union_list():
    query = """
    query GetUserMedia {
      user {
        id
        media {
            __typename
            ... on Audio {
              id
              duration
            }
            ... on Video {
              id
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
                {'__typename': 'Audio', 'id': 1, 'duration': '1s'},
                {'__typename': 'Video', 'id': 2, 'thumbnailUrl': '/video/2'},
            ]
        }
    }


def test_query_with_inline_fragment_and_fragment_spread():
    query = """
    query GetMedia {
      media {
        __typename
        ...AudioFragment
        ... on Video {
          id
          thumbnailUrl(size: 100)
        }
      }
    }
    
    fragment AudioFragment on Audio {
        id
        duration
    }
    """
    result = execute(GRAPH, read(query))
    assert result == {
        'media': {'__typename': 'Audio', 'id': 1, 'duration': '1s'},
    }


def test_query_only_one_union_type():
    query = """
    query GetMedia {
      media {
        __typename
        ... on Audio {
            id
            duration
        }
      }
    }

    """
    result = execute(GRAPH, read(query))
    assert result == {
        'media': {'__typename': 'Audio', 'id': 1, 'duration': '1s'},
    }


def test_query_only_typename():
    query = """
    query GetMedia {
      media {
        __typename
      }
    }

    """
    result = execute(GRAPH, read(query))
    assert result == {
        'media': {'__typename': 'Audio'},
    }


def test_validate_query_can_not_contain_shared_fields_in_union():
    query = """
    query SearchMedia($text: String) {
      searchMedia(text: $text) {
        __typename
        id
        ... on Audio {
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
        "Cannot query field 'id' on type 'Media'. "
        "Did you mean to use an inline fragment on 'Audio' or 'Video'?"
    ]


def test_validate_query_fragment_no_type_condition():
    query = """
    query SearchMedia($text: String) {
      searchMedia(text: $text) {
        ... {
          duration
        }
      }
    }
    """

    errors = validate(GRAPH, read(query, {'text': 'foo'}))

    assert errors == [
        "Cannot query field 'duration' on type 'Media'. "
        "Did you mean to use an inline fragment on 'Audio' or 'Video'?"
    ]


def test_validate_query_fragment_on_unknown_type():
    query = """
    query SearchMedia($text: String) {
      searchMedia(text: $text) {
        ... on X {
          duration
        }
      }
    }
    """

    errors = validate(GRAPH, read(query, {'text': 'foo'}))

    assert errors == ["Fragment on unknown type 'X'"]


def test_validate_union_type_has_no_field():
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


def test_validate_union_type_field_has_no_such_option():
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


def test_validate_query_can_contain_shared_links():
    query = """
    query SearchMedia($text: String) {
      searchMedia(text: $text) {
        __typename
        ... on Audio {
          duration
          user {
            id
          }
        }
        ... on Video {
          thumbnailUrl(size: 100)
        }
      }
    }
    """

    errors = validate(GRAPH, read(query, {'text': 'foo'}))
    assert not errors