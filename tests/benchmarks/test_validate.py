"""Benchmark query validation in isolation.

Validation (hiku.validate.query.validate) runs on every uncached request,
walking the query AST against the graph definition to check field existence,
link targets, option types, fragment applicability, and duplicate detection.

This benchmark isolates validation from parsing, merging, and execution.
We pre-parse each query to obtain the AST, then benchmark only validate().

Two graph sizes are tested:
- Standard (4 nodes): Company -> Department -> Employee -> Profile
- Wide (20 nodes, 10 fields each): stresses graph traversal at scale
"""

import pytest

from hiku.executors.sync import SyncExecutor
from hiku.graph import Field, Graph, Link, Node, Option, Root
from hiku.readers.graphql import parse_query, read_operation
from hiku.schema import Schema
from hiku.types import Integer, Optional, Sequence, String, TypeRef
from hiku.validate.query import validate


def _noop_resolver(fields, ids):
    return [[None] * len(fields) for _ in ids]


def _noop_root_resolver(fields):
    return [None] * len(fields)


def _noop_link():
    return []


def _noop_link_req(ids):
    return [[] for _ in ids]


def _noop_link_one(ids):
    return list(ids)


def _make_standard_graph():
    return Graph(
        [
            Node(
                "Company",
                [
                    Field("id", Integer, _noop_resolver),
                    Field("name", String, _noop_resolver),
                    Field("founded", Integer, _noop_resolver),
                    Field("revenue", Integer, _noop_resolver),
                    Link(
                        "departments",
                        Sequence[TypeRef["Department"]],
                        _noop_link_req,
                        requires="id",
                    ),
                ],
            ),
            Node(
                "Department",
                [
                    Field("id", Integer, _noop_resolver),
                    Field("name", String, _noop_resolver),
                    Field("budget", Integer, _noop_resolver),
                    Field("floor", Integer, _noop_resolver),
                    Link(
                        "employees",
                        Sequence[TypeRef["Employee"]],
                        _noop_link_req,
                        requires="id",
                    ),
                ],
            ),
            Node(
                "Employee",
                [
                    Field("id", Integer, _noop_resolver),
                    Field("name", String, _noop_resolver),
                    Field("email", String, _noop_resolver),
                    Field("role", String, _noop_resolver),
                    Field("salary", Integer, _noop_resolver),
                    Link(
                        "profile",
                        TypeRef["Profile"],
                        _noop_link_one,
                        requires="id",
                    ),
                ],
            ),
            Node(
                "Profile",
                [
                    Field("id", Integer, _noop_resolver),
                    Field("bio", String, _noop_resolver),
                    Field("avatar", String, _noop_resolver),
                    Field("website", String, _noop_resolver),
                    Field("joined_at", String, _noop_resolver),
                ],
            ),
            Root(
                [
                    Link(
                        "companies",
                        Sequence[TypeRef["Company"]],
                        _noop_link,
                        requires=None,
                    ),
                ]
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Wide graph (20 nodes, 10 fields each, linked in chain + cross-links)
# ---------------------------------------------------------------------------


def _make_wide_graph():
    n_nodes = 20
    fields_per_node = 10

    nodes = []
    for i in range(n_nodes):
        fields = [
            Field("id", Integer, _noop_resolver),
        ]
        for j in range(1, fields_per_node):
            fields.append(
                Field(
                    f"field_{j}",
                    String if j % 2 == 0 else Integer,
                    _noop_resolver,
                    options=(
                        [Option("limit", Optional[Integer], default=10)]
                        if j == 1
                        else None
                    ),
                )
            )
        # chain link to next node
        if i < n_nodes - 1:
            fields.append(
                Link(
                    "next",
                    Sequence[TypeRef[f"Node{i + 1}"]],
                    _noop_link_req,
                    requires="id",
                )
            )
        nodes.append(Node(f"Node{i}", fields))

    root_links = [
        Link(
            f"node{i}",
            Sequence[TypeRef[f"Node{i}"]],
            _noop_link,
            requires=None,
        )
        for i in range(n_nodes)
    ]
    nodes.append(Root(root_links))
    return Graph(nodes)


def parse_to_ast(query_str):
    """Parse a GraphQL query string into a hiku query AST."""
    doc = parse_query(query_str)
    op = read_operation(doc, None, None)
    return op.query


@pytest.fixture(name="std_graph")
def std_graph_fixture():
    schema = Schema(SyncExecutor(), _make_standard_graph())
    return schema.graph


@pytest.fixture(name="wide_graph")
def wide_graph_fixture():
    schema = Schema(SyncExecutor(), _make_wide_graph())
    return schema.graph


@pytest.fixture(name="query_shallow")
def query_shallow_fixture():
    return parse_to_ast("""
    {
        companies {
            name
            founded
        }
    }
    """)


@pytest.fixture(name="query_deep")
def query_deep_fixture():
    return parse_to_ast("""
    {
        companies {
            name
            founded
            revenue
            departments {
                name
                budget
                floor
                employees {
                    name
                    email
                    role
                    salary
                    profile {
                        bio
                        avatar
                        website
                        joined_at
                    }
                }
            }
        }
    }
    """)


@pytest.fixture(name="query_deep_inline_fragments")
def query_deep_inline_fragments_fixture():
    return parse_to_ast("""
    {
        companies {
            name
            ... on Company {
                founded
                revenue
                departments {
                    name
                    ... on Department {
                        budget
                        floor
                        employees {
                            name
                            ... on Employee {
                                email
                                role
                                salary
                                profile {
                                    bio
                                    ... on Profile {
                                        avatar
                                        website
                                        joined_at
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """)


@pytest.fixture(name="query_deep_named_fragments")
def query_deep_named_fragments_fixture():
    return parse_to_ast("""
    query {
        companies {
            ...CompanyBasic
            ...CompanyFull
        }
    }

    fragment CompanyBasic on Company {
        name
        founded
    }

    fragment CompanyFull on Company {
        name
        revenue
        departments {
            ...DeptBasic
            ...DeptFull
        }
    }

    fragment DeptBasic on Department {
        name
        budget
    }

    fragment DeptFull on Department {
        name
        floor
        employees {
            ...EmpBasic
            ...EmpFull
        }
    }

    fragment EmpBasic on Employee {
        name
        email
    }

    fragment EmpFull on Employee {
        name
        role
        salary
        profile {
            ...ProfileBasic
            ...ProfileFull
        }
    }

    fragment ProfileBasic on Profile {
        bio
        avatar
    }

    fragment ProfileFull on Profile {
        bio
        website
        joined_at
    }
    """)


@pytest.fixture(name="query_wide_shallow")
def query_wide_shallow_fixture():
    """Query 5 root links, 3 fields each — wide but shallow."""
    fields = " ".join(f"field_{j}" for j in range(1, 4))
    links = "\n".join(f"node{i} {{ id {fields} }}" for i in range(5))
    return parse_to_ast(f"{{ {links} }}")


@pytest.fixture(name="query_wide_deep")
def query_wide_deep_fixture():
    """Traverse 5 levels deep through the wide graph's chain links."""
    return parse_to_ast("""
    {
        node0 {
            id
            field_1(limit: 5)
            field_2
            field_3
            next {
                id
                field_1
                field_2
                next {
                    id
                    field_1
                    field_2
                    next {
                        id
                        field_1
                        field_2
                        next {
                            id
                            field_1
                            field_2
                            field_3
                            field_4
                        }
                    }
                }
            }
        }
    }
    """)


# ---------------------------------------------------------------------------
# Benchmarks — standard graph
# ---------------------------------------------------------------------------


def test_validate_shallow(benchmark, std_graph, query_shallow):
    """1 level: root -> companies (2 fields)."""
    errors = benchmark.pedantic(
        validate,
        args=(std_graph, query_shallow),
        iterations=10,
        rounds=5000,
    )
    assert errors == []


def test_validate_deep(benchmark, std_graph, query_deep):
    """4 levels: 15 fields across 4 node types."""
    errors = benchmark.pedantic(
        validate,
        args=(std_graph, query_deep),
        iterations=10,
        rounds=5000,
    )
    assert errors == []


def test_validate_deep_inline_fragments(
    benchmark, std_graph, query_deep_inline_fragments
):
    """4 levels with inline fragments — exercises visit_fragment path."""
    errors = benchmark.pedantic(
        validate,
        args=(std_graph, query_deep_inline_fragments),
        iterations=10,
        rounds=5000,
    )
    assert errors == []


def test_validate_deep_named_fragments(
    benchmark, std_graph, query_deep_named_fragments
):
    """4 levels with overlapping named fragments — duplicate field checking."""
    errors = benchmark.pedantic(
        validate,
        args=(std_graph, query_deep_named_fragments),
        iterations=10,
        rounds=5000,
    )
    assert errors == []


# ---------------------------------------------------------------------------
# Benchmarks — wide graph (20 nodes)
# ---------------------------------------------------------------------------


def test_validate_wide_graph_shallow(benchmark, wide_graph, query_wide_shallow):
    """Wide graph: 5 root links, 3 fields each — tests lookup in large graph."""
    errors = benchmark.pedantic(
        validate,
        args=(wide_graph, query_wide_shallow),
        iterations=10,
        rounds=5000,
    )
    assert errors == []


def test_validate_wide_graph_deep(benchmark, wide_graph, query_wide_deep):
    """Wide graph: 5-level chain traversal with options — tests deep validation
    in a graph with many nodes."""
    errors = benchmark.pedantic(
        validate,
        args=(wide_graph, query_wide_deep),
        iterations=10,
        rounds=5000,
    )
    assert errors == []
