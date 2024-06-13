from collections import deque
from contextlib import contextmanager
import typing as t

from collections.abc import Sequence

from hiku.enum import BaseEnum
from hiku.graph import Graph, Interface, Link as GraphLink, LinkType, Union
from hiku.query import Link, Field, Fragment, Node, QueryVisitor
from hiku.types import (
    InterfaceRefMeta,
    OptionalMeta,
    Record,
    RecordMeta,
    RefMeta,
    SequenceMeta,
    TypeRefMeta,
    UnionRefMeta,
    get_type,
)


def get_ref_type(types, type_, name):
    if isinstance(type_, RecordMeta):
        type_ = type_.__field_types__[name]
        if isinstance(type_, TypeRefMeta):
            return type_
        elif isinstance(type_, SequenceMeta):
            type_ref = type_.__item_type__
            if isinstance(type_ref, OptionalMeta):  # Ref ?
                type_ref = type_ref.__type__
            assert isinstance(type_ref, RefMeta), type_ref
            return type_ref
        elif isinstance(type_, InterfaceRefMeta):
            return type_
        elif isinstance(type_, OptionalMeta):
            return type_.__type__
        return get_ref_type(types, type_.__field_types__[name], name)
    elif isinstance(type_, UnionRefMeta):
        # TODO: finish
        return type_
    elif isinstance(type_, InterfaceRefMeta):
        # TODO: finish
        return type_
    elif isinstance(type_, TypeRefMeta):
        type_ = get_type(types, type_)
        return get_ref_type(types, type_, name)
    else:
        raise AssertionError(repr(type_))


class QueryMerger(QueryVisitor):
    def __init__(self, graph: Graph):
        self.graph = graph
        self._types = graph.__types__
        self._type: t.Deque[
            t.Union[t.Type[Record], Union, Interface, BaseEnum]
        ] = deque([self._types["__root__"]])

        self._visited_fields = deque([set()])

    def merge(self, query: Node) -> Node:
        return self.visit(query)

    @property
    def parent_type(
        self,
    ) -> t.Union[t.Type[Record], Union, Interface, BaseEnum]:
        return self._type[-1]

    @contextmanager
    def with_type_info(self, obj: Link):
        ref_type = get_ref_type(self._types, self._type[-1], obj.name)

        self._type.append(ref_type)
        yield
        self._type.pop()

    def visit_node(self, node: Node) -> None:
        return self._merge_nodes([node])

    def _collect_fields(self, node: Node, fields, links, fragments) -> None:
        for field in node.fields:
            name = field.alias or field.name

            if isinstance(field, Field):
                if name not in self._visited_fields[-1]:
                    fields[name] = field
            elif isinstance(field, Link):
                links.setdefault(name, []).append(field)

        fragments_by_type_name = {}

        # TODO: determine fragments parsing rules
        for fr in node.fragments:
            if is_fragment_condition_match(self.graph, self.parent_type, fr):
                self._collect_fields(fr.node, fields, links, fragments)
            else:
                fragments_by_type_name.setdefault(fr.type_name, []).append(fr)

        for frs in fragments_by_type_name.values():
            fragments.append(self._merge_fragments(frs))

    def visit_link(self, obj: Link) -> t.Any:
        with self.with_type_info(obj):
            return super().visit_link(obj)

    def _merge_fragments(self, fragments: t.List[Fragment]) -> Fragment:
        fr = fragments[0]
        new = Fragment(
            fr.name,
            fr.type_name,
            self._merge_nodes([fr.node for fr in fragments]).fields,
        )
        return new

    def _merge_nodes(self, nodes: t.List[Node]) -> Node:
        """Collect fields from multiple nodes and return new node with them.
        The main difference from `merge` is that it collects fields
        from fragments and drops fragments.
        """
        assert isinstance(nodes, Sequence), type(nodes)
        ordered = any(n.ordered for n in nodes)

        fields_map = {}
        links_map = {}
        fragments = []

        for node in nodes:
            self._collect_fields(node, fields_map, links_map, fragments)

        fields = []
        for field in fields_map.values():
            fields.append(field)

        for links in links_map.values():
            fields.append(self._merge_links(links))

        return Node(fields=fields, fragments=fragments, ordered=ordered)

    def _merge_links(self, links: t.List[Link]) -> Link:
        """Recursively merge link node fields and return new link"""
        link = links[0]

        directives = []
        for link in links:
            directives.extend(link.directives)

        with self.with_type_info(link):
            return link.copy(
                node=self._merge_nodes([link.node for link in links]),
                directives=tuple(directives),
            )


def is_abstract_link(graphql_link: GraphLink) -> bool:
    return graphql_link.type_info.type_enum in (
        LinkType.UNION,
        LinkType.INTERFACE,
    )


def is_fragment_condition_match(
    graph: Graph,
    runtime_type,
    fragment: Fragment,
) -> bool:
    """Check if a fragment is applicable to the given type."""
    type_name = fragment.type_name
    if not type_name:
        return True

    if isinstance(runtime_type, TypeRefMeta):
        if type_name == runtime_type.__type_name__:
            return True

    if isinstance(runtime_type, UnionRefMeta):
        # We do not merge abstract type fragmetns, but we must merge same cocrete type fragments
        return False
        union = graph.unions_map[runtime_type.__type_name__]
        return type_name in union.types
    if isinstance(runtime_type, InterfaceRefMeta):
        return False
        interface_types = graph.interfaces_types[runtime_type.__type_name__]
        return type_name in interface_types

    return False
