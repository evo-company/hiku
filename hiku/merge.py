import typing as t

from collections import defaultdict, deque
from contextlib import contextmanager
from collections.abc import Sequence

from hiku.directives import Directive
from hiku.graph import Graph, Interface
from hiku.query import FieldOrLink, Link, Field, Fragment, Node, QueryVisitor
from hiku.types import (
    InterfaceRefMeta,
    OptionalMeta,
    Record,
    RecordMeta,
    RefMeta,
    RefMetaTypes,
    SequenceMeta,
    TypeRefMeta,
    Types,
    UnionRefMeta,
    get_type,
)


def get_ref_type(
    types: Types, type_: t.Union[t.Type[Record], RefMetaTypes], name: str
) -> RefMetaTypes:
    if isinstance(type_, RecordMeta):
        type_ = type_.__field_types__[name]
        if isinstance(type_, TypeRefMeta):
            return type_

        return get_ref_type(types, type_, name)
    elif isinstance(type_, OptionalMeta):
        assert isinstance(type_.__type__, RefMeta), type_.__type__
        return type_.__type__
    elif isinstance(type_, UnionRefMeta):
        return type_
    elif isinstance(type_, InterfaceRefMeta):
        return type_
    elif isinstance(type_, TypeRefMeta):
        type_ = get_type(types, type_)
        return get_ref_type(types, type_, name)
    elif isinstance(type_, SequenceMeta):
        type_ref = type_.__item_type__
        if isinstance(type_ref, OptionalMeta):
            type_ref = type_ref.__type__
        assert isinstance(type_ref, RefMeta), type_ref
        return type_ref
    else:
        raise AssertionError(repr(type_))


def is_match_type(
    type_: t.Union[t.Type[Record], RefMetaTypes], fragment: Fragment
) -> bool:
    if fragment.type_name is None:
        return True

    if isinstance(type_, RecordMeta):
        return False

    return fragment.type_name == type_.__type_name__


class QueryMerger(QueryVisitor):
    def __init__(self, graph: Graph):
        self.graph = graph
        self._types = graph.__types__
        self._type: t.Deque[t.Union[t.Type[Record], RefMetaTypes]] = deque(
            [self._types["__root__"]]
        )

    def merge(self, query: Node) -> Node:
        """Merge query node and return new node with merged fields, links
        and fragments.

        Must be called after the query is validated since we assume that
        no two fields with the same name+alias are present in same node.
        """
        return self.visit(query)

    @property
    def parent_type(
        self,
    ) -> t.Union[t.Type[Record], RefMetaTypes]:
        return self._type[-1]

    @contextmanager
    def _with_type_info(self, obj: Link) -> t.Iterator[None]:
        ref_type = get_ref_type(self._types, self._type[-1], obj.name)

        self._type.append(ref_type)
        yield
        self._type.pop()

    def visit_node(self, node: Node) -> Node:
        return self._merge_nodes([node])

    def visit_link(self, obj: Link) -> t.Any:
        with self._with_type_info(obj):
            return super().visit_link(obj)

    def _collect_fields(
        self,
        node: Node,
        fields: t.Dict[str, Field],
        links: t.Dict[str, t.List[Link]],
        fragments: t.List[Fragment],
    ) -> None:
        """Collect fields, links and fragments from the node.

        Fields collected in the fields dict. It is safe to assume that after
        validation, there is no possibility of having two fields with the same
        name+alias in the same node, hence we can use alias(or name) as a key.
        """
        for field in node.fields:
            name = field.alias or field.name

            if isinstance(field, Field):
                if name not in fields:
                    fields[name] = field
            elif isinstance(field, Link):
                links.setdefault(name, []).append(field)

        fragments_to_process: t.List[Fragment] = []
        for fr in node.fragments:
            if is_match_type(self.parent_type, fr):
                self._expand_fragment(fr, fields, links, fragments_to_process)
            else:
                fragments_to_process.append(fr)

        self._merge_fragments(
            fragments_to_process,
            fields,
            links,
            fragments,
        )

    def _collect_interface_fields(
        self,
        fragment: Fragment,
        interface: Interface,
        fields: t.Dict[str, Field],
        links: t.Dict[str, t.List[Link]],
    ) -> t.Optional[Fragment]:
        """For interface fragment, we collect/extract fields that are
        declared in the interface. The rest of the fields are left in
        the fragment.
        """
        fragment_fields: t.List[FieldOrLink] = []

        for field in fragment.node.fields:
            name = field.alias or field.name
            is_interface_field = name in interface.fields_map
            if isinstance(field, Field):
                if is_interface_field:
                    if name not in fields:
                        fields[name] = field
                else:
                    fragment_fields.append(field)
            elif isinstance(field, Link):
                if is_interface_field:
                    links.setdefault(name, []).append(field)
                else:
                    fragment_fields.append(field)

        if fragment_fields:
            return fragment.copy(node=Node(fragment_fields))

        return None

    def _merge_fragments(
        self,
        fragments_to_process: t.List[Fragment],
        fields: t.Dict[str, Field],
        links: t.Dict[str, t.List[Link]],
        fragments: t.List[Fragment],
    ) -> None:
        """Merge fragments. Depending on the type of the parent type,
        the fragments are merged differently.

        For example for interfaces/unions we apply diffrent logic when
        collecting fields and links.
        """
        fragments_by_type: t.DefaultDict[str, t.List[Fragment]] = defaultdict(
            list
        )

        for fragment in fragments_to_process:
            if fragment.type_name is None or (
                isinstance(self.parent_type, TypeRefMeta)
                and fragment.type_name == self.parent_type.__type_name__
            ):
                self._collect_fields(fragment.node, fields, links, fragments)
            elif isinstance(self.parent_type, InterfaceRefMeta):
                assert fragment.type_name is not None
                new_fragment = self._collect_interface_fields(
                    fragment,
                    self.graph.interfaces_map[self.parent_type.__type_name__],
                    fields,
                    links,
                )
                if new_fragment is not None:
                    fragments_by_type[fragment.type_name].append(new_fragment)
            else:
                # for the rest of the cases(including unions), we just collect
                # fragments and then merge them by type reducing duplicates
                fragments_by_type[fragment.type_name].append(fragment)

        for frs in fragments_by_type.values():
            fragments.append(self._merge_same_type_fragments(frs))

    def _merge_same_type_fragments(
        self, fragments: t.List[Fragment]
    ) -> Fragment:
        return fragments[0].copy(
            node=self._merge_nodes([fr.node for fr in fragments]),
        )

    def _expand_fragment(
        self,
        fragment: Fragment,
        fields: t.Dict[str, Field],
        links: t.Dict[str, t.List[Link]],
        fragments: t.List[Fragment],
    ) -> None:
        """Given a fragment, expand it and collect fields, links and fragments.
        Fragment is disposed.
        Example, expand QueryFragment:
        Given:
            query { ...QueryFragment }
            fragment QueryFragment on Query { id ... on Query { name } }
        Result:
            query { id name }
        """
        for field in fragment.node.fields:
            name = field.alias or field.name

            if isinstance(field, Field):
                if name not in fields:
                    fields[name] = field
            elif isinstance(field, Link):
                links.setdefault(name, []).append(field)

        for fr in fragment.node.fragments:
            fragments.append(fr)

    def _merge_nodes(self, nodes: t.List[Node]) -> Node:
        """Collect fields from multiple nodes and return new node with them"""
        assert isinstance(nodes, Sequence), type(nodes)
        ordered = any(n.ordered for n in nodes)

        fields_map: t.Dict[str, Field] = {}
        links_map: t.Dict[str, t.List[Link]] = {}
        fragments: t.List[Fragment] = []

        for node in nodes:
            self._collect_fields(node, fields_map, links_map, fragments)

        fields: t.List[FieldOrLink] = []
        for field in fields_map.values():
            fields.append(field)

        for links in links_map.values():
            fields.append(self._merge_links(links))

        return Node(fields=fields, fragments=fragments, ordered=ordered)

    def _merge_links(self, links: t.List[Link]) -> Link:
        """Recursively merge link node fields and return new link"""
        link = links[0]

        directives: t.List[Directive] = []
        for link in links:
            directives.extend(link.directives)

        with self._with_type_info(link):
            return link.copy(
                node=self._merge_nodes([link.node for link in links]),
                directives=tuple(directives),
            )
