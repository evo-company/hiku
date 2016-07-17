from hiku import query as q
from hiku.graph import Graph, Edge, Field, Link, Option, Root, MANY
from hiku.types import Integer
from hiku.validate.query import QueryValidator


def _():
    return 1/0


# TODO: refactor
GRAPH = Graph([
    Edge('e1', [
        Field('f2', Integer, _,
              options=[Option('f2-op1', Integer),
                       Option('f2-op2', Integer, default=1)]),
        Link('l1', MANY, _, edge='e2', requires='f2',
             options=[Option('l1-op1', Integer),
                      Option('l1-op2', Integer, default=1)]),
    ]),
    Edge('e2', [
        Field('f3', _),
    ]),
    Root([
        Field('f1', Integer, _),
        Edge('e1', [
            Field('f2', Integer, _,
                  options=[Option('f2-op1', Integer),
                           Option('f2-op2', Integer, default=1)]),
            Link('l1', MANY, _, edge='e2', requires='f2',
                 options=[Option('l1-op1', Integer),
                          Option('l1-op2', Integer, default=1)]),
        ]),
        Edge('e2', [
            Field('f3', _),
        ]),
        Link('l2', MANY, _, edge='e2', requires=None),
    ]),
])


def check_errors(query, errors):
    validator = QueryValidator(GRAPH)
    validator.visit(query)
    assert validator.errors.list == errors


def test_field():
    # field in the root edge
    check_errors(q.Edge([q.Field('invalid')]), [
        'Field "invalid" is not implemented in the "root" edge',
    ])
    # field in the global edge
    check_errors(q.Edge([q.Link('e1', q.Edge([q.Field('invalid')]))]), [
        'Field "invalid" is not implemented in the "e1" edge',
    ])
    # field in the linked edge
    check_errors(q.Edge([q.Link('l2', q.Edge([q.Field('invalid')]))]), [
        'Field "invalid" is not implemented in the "e2" edge',
    ])


def test_non_field():
    check_errors(q.Edge([q.Field('l2')]), [
        'Trying to query "root.l2" link as it was a field',
    ])
    check_errors(q.Edge([q.Field('e2')]), [
        'Trying to query "e2" edge as it was a field',
    ])


def test_field_options():
    def mk(**kwargs):
        return q.Edge([q.Link('e1', q.Edge([q.Field('f2', **kwargs)]))])

    check_errors(mk(), [
        'Required option "e1.f2:f2-op1" is not specified',
    ])
    check_errors(mk(options={'f2-op1': 1, 'invalid': 2}), [
        'Unknown options for "e1.f2": invalid',
    ])
    check_errors(mk(options={'f2-op1': '1'}), [
        'Invalid type "str" for option "e1.f2:f2-op1" provided',
    ])


def test_link():
    l = q.Link('invalid', q.Edge([]))
    # link in the root edge
    check_errors(q.Edge([l]), [
        'Link "invalid" is not implemented in the "root" edge',
    ])
    # link in the global edge
    check_errors(q.Edge([q.Link('e1', q.Edge([l]))]), [
        'Link "invalid" is not implemented in the "e1" edge',
    ])
    # link in the linked edge
    check_errors(q.Edge([q.Link('l2', q.Edge([l]))]), [
        'Link "invalid" is not implemented in the "e2" edge',
    ])


def test_non_link():
    check_errors(q.Edge([q.Link('f1', q.Edge([]))]), [
        'Trying to query "root.f1" field as edge',
    ])


def test_link_options():
    def mk(**kwargs):
        return q.Edge([q.Link('e1', q.Edge([q.Link('l1', q.Edge([]),
                                                   **kwargs)]))])

    check_errors(mk(), [
        'Required option "e1.l1:l1-op1" is not specified',
    ])
    check_errors(mk(options={'l1-op1': 1, 'invalid': 2}), [
        'Unknown options for "e1.l1": invalid',
    ])
    check_errors(mk(options={'l1-op1': '1'}), [
        'Invalid type "str" for option "e1.l1:l1-op1" provided',
    ])
