import pytest

from hiku.denormalize.graphql import DenormalizeGraphQL
from hiku.engine import Engine, SplitUnionByNodes
from hiku.executors.sync import SyncExecutor
from hiku.graph import Field, Graph, Link, Node, Option, Root, Union
from hiku.types import Integer, Optional, Sequence, String, TypeRef, UnionRef
from hiku.utils import listify
from hiku.readers.graphql import read
from hiku.validate.graph import GraphValidationError
from hiku.validate.query import validate


def execute(graph, query):
    engine = Engine(SyncExecutor())
    result = engine.execute(graph, query, {})
    return DenormalizeGraphQL(graph, result, "query").process(query)


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
    ]),
    Node('Video', [
        Field('id', Integer, resolve_video_fields),
        Field('thumbnailUrl', String, resolve_video_fields),
    ]),
    Union(
        'Media', ['Audio', 'Video']
    ),
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
    ]),
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
            Union(
                'Media', []
            ),
            Union(
                '', ['Audio', 'Video']
            ),

            Union(
                'Invalid', ['Unknown']
            ),
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
        ])

    assert err.value.errors == [
        'Union must have at least one type',
        'Union must have a name',
        "Union 'Invalid' types '['Unknown']' must point to node or data type",
    ]


def test_query_union_list():
    query = """
    query SearchMedia($text: String) {
      searchMedia(text: $text) {
        __typename
        ... on Audio {
          duration
        }
        ... on Video {
          thumbnailUrl
        }
      }
    }
    """
    result = execute(GRAPH, read(query, {'text': 'foo'}))
    assert result == {
        'searchMedia': [
            {'__typename': 'Audio', 'duration': '1s'},
            {'__typename': 'Video', 'thumbnailUrl': '/video/2'},
            {'__typename': 'Audio', 'duration': '3s'},
            {'__typename': 'Video', 'thumbnailUrl': '/video/4'},
        ]
    }


def test_query_union_one():
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
    result = execute(GRAPH, read(query))
    assert result == {
        'media': {'__typename': 'Audio', 'id': 1, 'duration': '1s'},
    }


def test_query_union_optional():
    query = """
    query MaybeGetMedia {
      maybeMedia {
        __typename
        ... on Audio {
          duration
        }
        ... on Video {
          thumbnailUrl
        }
      }
    }
    """
    result = execute(GRAPH, read(query))
    assert result == {
        'maybeMedia': {'__typename': 'Video', 'thumbnailUrl': '/video/2'},
    }


def test_validate_query_can_not_contain_shared_fields():
    query = """
    query SearchMedia($text: String) {
      searchMedia(text: $text) {
        id
        ... on Audio {
          duration
        }
        ... on Video {
          thumbnailUrl
        }
      }
    }
    """

    errors = validate(GRAPH, read(query, {'text': 'foo'}))

    assert errors == [
        "Cannot query field 'id' on type 'Media'. "
        "Did you mean to use an inline fragment on 'Audio' or 'Video'?"
    ]


def test_validate_union_type_has_no_field():
    query = """
    query SearchMedia($text: String) {
      searchMedia(text: $text) {
        ... on Audio {
          invalid_field
          duration
        }
        ... on Video {
          thumbnailUrl
        }
      }
    }
    """

    errors = validate(GRAPH, read(query, {'text': 'foo'}))

    # TODO: improv error message, specify which type has no such field
    assert errors == [
        'Field "invalid_field" is not found in any of the types of union "Media"',
    ]


def test_validate_union_type_has_no_option():
    query = """
    query SearchMedia($text: String) {
      searchMedia(text: $text) {
        ... on Audio {
          duration
        }
        ... on Video {
          thumbnailUrl(size: "40x40")
        }
      }
    }
    """

    errors = validate(GRAPH, read(query, {'text': 'foo'}))

    assert errors == [
        'Unknown options for "Video.thumbnailUrl": size',
    ]


def test_split_union_into_nodes():
    query_raw = """
    query SearchMedia($text: String) {
      searchMedia(text: $text) {
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
    query = read(query_raw, {'text': 'foo'})

    nodes = SplitUnionByNodes(GRAPH, GRAPH.unions_map['Media']).split(
        query.fields_map['searchMedia'].node
    )

    assert len(nodes) == 2

    assert 'Audio' in nodes
    assert 'Video' in nodes

    assert nodes['Audio'].fields_map.keys() == {'id', 'duration'}
    assert nodes['Video'].fields_map.keys() == {'id', 'thumbnailUrl'}
