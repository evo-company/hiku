import typing as t
from collections import defaultdict
from inspect import isawaitable

from graphql import parse as gql_parse
from graphql.language import ast as gql_ast

from hiku.compat import TypeAlias
from hiku.directives import SchemaDirective
from hiku.federation.directive import Requires
from hiku.engine import pass_context
from hiku.enum import BaseEnum
from hiku.federation.scalars import FieldSet, LinkImport, _Any
from hiku.federation.utils import get_entity_types
from hiku.federation.version import DEFAULT_FEDERATION_VERSION
from hiku.graph import Field
from hiku.graph import Graph as _Graph
from hiku.graph import (
    GraphTransformer,
    Input,
    Interface,
    Link,
    Node,
    Option,
    Root,
    Union,
)
from hiku.scalar import Scalar
from hiku.types import Optional, Record, Sequence, String, TypeRef, UnionRef

RawRef: TypeAlias = t.Any


class FederatedNode(Node):
    def __init__(
        self,
        name: str | None,
        fields: list[Field | Link],
        *,
        description: str | None = None,
        directives: t.Sequence[SchemaDirective] | None = None,
        resolve_reference: t.Callable[[list[dict]], list[RawRef]] | None = None,
    ):
        super().__init__(
            name, fields, description=description, directives=directives
        )
        self.resolve_reference = resolve_reference


class ReferenceEntry:
    __slots__ = ("index", "typename", "reference")

    def __init__(self, index: int, typename: str, reference: RawRef):
        self.index = index
        self.typename = typename
        self.reference = reference


def to_reference(entry: ReferenceEntry) -> tuple[dict, type[TypeRef]]:
    return entry.reference, TypeRef[entry.typename]


class GraphInit(GraphTransformer):
    type_to_resolve_reference_map: dict[str, t.Callable]
    is_async: bool
    has_entity_types: bool

    @classmethod
    def init(
        cls,
        items: list[FederatedNode | Node],
        is_async: bool,
        has_entity_types: bool = False,
    ) -> list[Node]:
        self = cls()
        self.type_to_resolve_reference_map = {}
        self.is_async = is_async
        self.has_entity_types = has_entity_types
        return [self.visit(i) for i in items]

    def visit_root(self, root: Root) -> Root:
        if not self.has_entity_types:
            return root

        fields = root.fields[:]
        if "_entities" not in root.fields_map:
            fields.append(self.entities_link())
        if "_service" not in root.fields_map:
            fields.append(self.service_field())

        return Root(fields)

    def visit_node(self, obj: Node) -> Node:
        if hasattr(obj, "resolve_reference") and obj.name is not None:
            self.type_to_resolve_reference_map[obj.name] = obj.resolve_reference
            self._validate_link_requires(obj)

        return super(GraphInit, self).visit_node(obj)

    @staticmethod
    def _field_set_names(field_set: str) -> set[str]:
        """Extract top-level field names from a GraphQL FieldSet string."""
        doc = gql_parse(f"{{ {field_set} }}")
        op = t.cast(gql_ast.OperationDefinitionNode, doc.definitions[0])
        return {
            sel.name.value
            for sel in op.selection_set.selections
            if isinstance(sel, gql_ast.FieldNode)
        }

    def _validate_link_requires(self, node: Node) -> None:
        """Raise ValueError if a Link's SDL @requires omits fields that are
        transitively required through its internal requires chain.
        """
        for graph_field in node.fields:
            if not isinstance(graph_field, Link):
                continue
            link = graph_field
            if not link.requires:
                continue

            # Collect field names declared in the Link's SDL @requires
            declared: set[str] = set()
            for d in link.directives:
                if isinstance(d, Requires):
                    declared.update(self._field_set_names(str(d.fields)))

            # Collect field names transitively required by fields
            # in Link.requires
            link_requires = (
                link.requires
                if isinstance(link.requires, list)
                else [link.requires]
            )
            missing: set[str] = set()
            for req_name in link_requires:
                sibling = node.fields_map.get(req_name)
                if not isinstance(sibling, Field):
                    continue
                for d in sibling.directives:
                    if isinstance(d, Requires):
                        for field_name in self._field_set_names(str(d.fields)):
                            if field_name not in declared:
                                missing.add(field_name)

            if missing:
                suggested = " ".join(sorted(declared | missing))
                raise ValueError(
                    f"Link {link.name!r} in node {node.name!r} declares "
                    f"requires={link.requires!r}, but the following fields "
                    f"are transitively required and missing from the Link's "
                    f"@requires directive: {sorted(missing)!r}. "
                    f"Update the directive to: Requires({suggested!r})"
                )
                suggested = " ".join(sorted(declared | missing))

    def _group_representations(
        self, representations: list[dict]
    ) -> defaultdict[str, list[tuple[int, dict]]]:
        repr_by_type = defaultdict(list)
        for idx, rep in enumerate(representations):
            typename = rep["__typename"]
            if typename not in self.type_to_resolve_reference_map:
                raise TypeError(
                    'Type "{}" must have "reference_resolver"'.format(typename)
                )

            # store index along with representation to sort references later
            repr_by_type[typename].append((idx, rep))
        return repr_by_type

    def _collect_reference_entries(
        self,
        typename: str,
        references: list[RawRef],
        representations: list[tuple[int, dict]],
    ) -> t.Iterator[ReferenceEntry]:
        for (idx, _), ref in zip(representations, references):
            # store index alongside reference and type
            # in order to sort references later and drop index
            yield ReferenceEntry(
                index=idx,
                typename=typename,
                reference=ref,
            )

    def _execute_resolve_reference(
        self, typename: str, type_representations: list[tuple[int, dict]]
    ) -> list[dict]:
        resolve_reference = self.type_to_resolve_reference_map[typename]
        return resolve_reference([rep for idx, rep in type_representations])

    def entities_link(self) -> Link:
        def entities_resolver(
            options: dict,
        ) -> list[tuple[t.Any, type[TypeRef]]]:
            representations = options["representations"]
            if not representations:
                return []

            repr_by_type = self._group_representations(representations)

            reference_entries: list[ReferenceEntry] = []

            for typename, type_representations in repr_by_type.items():
                refs = self._execute_resolve_reference(
                    typename, type_representations
                )
                reference_entries.extend(
                    self._collect_reference_entries(
                        typename, refs, type_representations
                    )
                )

            return list(
                map(
                    to_reference,
                    sorted(reference_entries, key=lambda e: e.index),
                )
            )

        async def entities_resolver_async(
            options: dict,
        ) -> list[tuple[t.Any, type[TypeRef]]]:
            representations = options["representations"]
            if not representations:
                return []

            repr_by_type = self._group_representations(representations)
            reference_entries: list[ReferenceEntry] = []

            for typename, type_representations in repr_by_type.items():
                refs = self._execute_resolve_reference(
                    typename, type_representations
                )
                if isawaitable(refs):
                    refs = await refs

                reference_entries.extend(
                    self._collect_reference_entries(
                        typename, refs, type_representations
                    )
                )

            return list(
                map(
                    to_reference,
                    sorted(reference_entries, key=lambda e: e.index),
                )
            )

        return Link(
            "_entities",
            Sequence[Optional[UnionRef["_Entity"]]],
            (entities_resolver_async if self.is_async else entities_resolver),
            options=[
                Option("representations", Sequence[_Any]),
            ],
            requires=None,
        )

    def service_field(self) -> Field:
        @pass_context
        def service_resolver(
            ctx: dict,
            fields: list,
        ) -> list:
            return [{"sdl": ctx["__sdl__"]}]

        def _async(func: t.Callable) -> t.Callable:
            @pass_context
            async def wrapper(*args: t.Any, **kwargs: t.Any) -> list[dict]:
                return func(*args, **kwargs)

            return wrapper

        return Field(
            "_service",
            TypeRef["_Service"],
            _async(service_resolver) if self.is_async else service_resolver,
        )


class Graph(_Graph):
    def __init__(
        self,
        items: list[FederatedNode | Node],
        data_types: dict[str, type[Record]] | None = None,
        directives: t.Sequence[type[SchemaDirective]] | None = None,
        unions: list[Union] | None = None,
        interfaces: list[Interface] | None = None,
        enums: list[BaseEnum] | None = None,
        scalars: list[type[Scalar]] | None = None,
        inputs: list[Input] | None = None,
        is_async: bool = False,
    ):
        self.is_async = is_async

        if unions is None:
            unions = []

        if scalars is None:
            scalars = []

        unions_map = {union.name: union for union in unions}
        scalars_map = {scalar.__type_name__: scalar for scalar in scalars}

        entity_types = get_entity_types(items, DEFAULT_FEDERATION_VERSION)
        if entity_types:
            if "_Entity" not in unions_map:
                unions.append(Union("_Entity", entity_types))

        for scalar in [_Any, FieldSet, LinkImport]:
            if scalar.__type_name__ not in scalars_map:
                scalars.append(scalar)

        if data_types is None:
            data_types = {}

        if "_Service" not in data_types:
            data_types["_Service"] = Record[{"sdl": String}]

        items = GraphInit.init(items, is_async, bool(entity_types))

        super().__init__(
            items,
            data_types,
            directives,
            unions,
            interfaces,
            enums,
            scalars,
            inputs,
        )

    @classmethod
    def from_graph(
        cls,
        other: "Graph",
        root: Root,
    ) -> "Graph":
        """Create graph from other graph, with new root node.
        Useful for creating mutation graph from query graph.
        """
        return cls(
            other.nodes + [root],
            data_types=other.data_types,
            directives=other.directives,
            unions=other.unions,
            interfaces=other.interfaces,
            enums=other.enums,
            scalars=other.scalars,
            inputs=other.inputs,
            is_async=other.is_async,
        )
