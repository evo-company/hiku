from enum import Enum
from typing import List

from hiku.directives import (
    Directive, Location, SchemaDirective, directive,
    directive_field, schema_directive, schema_directive_field
)
from hiku.enum import enum
from hiku.graph import Field, Graph, Link, Node, Root, apply
from hiku.introspection.graphql import GraphQLIntrospection
from hiku.introspection.types import ENUM, LIST, NON_NULL, SCALAR
from hiku.types import Integer, TypeRef


@enum(name='Custom_Options')
class Options(Enum):
    A = 'a'
    B = 'b'


def test_directive_has_info():
    @directive(
        name='custom',
        locations=[Location.FIELD],
        description='Custom directive'
    )
    class Custom(Directive):
        from_: str = directive_field(name='from')
        options: List[Options] = directive_field()

    custom = Custom(
        from_='some text',
        options=[Options.A],
    )

    assert custom.from_ == 'some text'
    assert custom.__directive_info__ is not None
    assert custom.__directive_info__.name == 'custom'
    assert custom.__directive_info__.locations == [Location.FIELD]
    assert custom.__directive_info__.description == 'Custom directive'

    assert len(custom.__directive_info__.args) == 2

    assert custom.__directive_info__.args[0].name == 'from_'
    assert custom.__directive_info__.args[0].field_name == 'from'
    assert custom.__directive_info__.args[0].type_ident == NON_NULL(SCALAR('String'))

    assert custom.__directive_info__.args[1].name == 'options'
    assert custom.__directive_info__.args[1].field_name == 'options'
    assert custom.__directive_info__.args[1].type_ident == NON_NULL(LIST(ENUM('Custom_Options', ['a', 'b'])))


def test_schema_directive_has_info():
    @schema_directive(
        name='custom',
        locations=[Location.SCHEMA],
        description='Custom directive'
    )
    class Custom(SchemaDirective):
        from_: str = schema_directive_field(name='from')

    custom = Custom(
        from_='some text',
    )

    assert custom.from_ == 'some text'
    assert custom.__directive_info__ is not None
    assert custom.__directive_info__.name == 'custom'
    assert custom.__directive_info__.locations == [Location.SCHEMA]
    assert custom.__directive_info__.description == 'Custom directive'

    assert len(custom.__directive_info__.args) == 1
    assert custom.__directive_info__.args[0].name == 'from_'
    assert custom.__directive_info__.args[0].field_name == 'from'
    assert custom.__directive_info__.args[0].type_ident == NON_NULL(SCALAR('String'))


def test_directives_hashable():
    @schema_directive(
        name='A',
        locations=[Location.SCHEMA]
    )
    class A(SchemaDirective):
        ...

    @schema_directive(
        name='B',
        locations=[Location.SCHEMA]
    )
    class B(SchemaDirective):
        ...

    directives = set()
    for d in [A(), B(), A()]:
        directives.add(d)

    assert directives == {A(), B()}


def test_custom_graph_directives():
    @schema_directive(
        name='custom',
        locations=[Location.FIELD_DEFINITION]
    )
    class Custom(SchemaDirective):
        text: str = schema_directive_field()

    GRAPH = Graph([
        Node('A', [
            Field('a', Integer, lambda: None, directives=[Custom('some text')]),
        ]),
        Root([
            Link('a', TypeRef['A'], lambda: None, requires=None),
        ]),
    ], directives=[Custom])

    GRAPH = apply(GRAPH, [
        GraphQLIntrospection(GRAPH),
    ])

    assert GRAPH.directives == (Custom,)
