"""Benchmark result denormalization in isolation.

DenormalizeGraphQL runs on every response, converting the engine's
normalized Index/Proxy representation into the nested dicts clients expect.
This benchmark isolates that step from parsing, validation, and execution.

The graph topology mirrors test_engine_execute.py:
    Root -> Company -> Department -> Employee -> Profile

We pre-execute each query once to obtain the Proxy result and merged
query AST, then benchmark only DenormalizeGraphQL.process().
"""

import pytest

from hiku.denormalize.graphql import DenormalizeGraphQL
from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.graph import Field, Graph, Link, Node, Root
from hiku.merge import QueryMerger
from hiku.operation import Operation, OperationType
from hiku.readers.graphql import parse_query, read_operation
from hiku.context import create_execution_context
from hiku.schema import Schema
from hiku.types import Integer, Sequence, String, TypeRef
from hiku.validate.query import validate


def make_graph(n_companies, n_depts, n_employees):
    """Build graph and link functions for the given data dimensions."""

    def resolve_company(fields, ids):
        def get(f, id_):
            if f.name == "id":
                return id_
            if f.name == "name":
                return f"Company {id_}"
            if f.name == "founded":
                return 2000 + id_
            if f.name == "revenue":
                return id_ * 1_000_000

        return [[get(f, i) for f in fields] for i in ids]

    def resolve_department(fields, ids):
        def get(f, id_):
            if f.name == "id":
                return id_
            if f.name == "name":
                return f"Department {id_}"
            if f.name == "budget":
                return id_ * 10_000
            if f.name == "floor":
                return id_ % 10

        return [[get(f, i) for f in fields] for i in ids]

    def resolve_employee(fields, ids):
        def get(f, id_):
            if f.name == "id":
                return id_
            if f.name == "name":
                return f"Employee {id_}"
            if f.name == "email":
                return f"emp{id_}@test.com"
            if f.name == "role":
                return "Engineer"
            if f.name == "salary":
                return 50_000 + id_ * 100

        return [[get(f, i) for f in fields] for i in ids]

    def resolve_profile(fields, ids):
        def get(f, id_):
            if f.name == "id":
                return id_
            if f.name == "bio":
                return f"Bio of {id_}"
            if f.name == "avatar":
                return f"https://avatar/{id_}"
            if f.name == "website":
                return f"https://site/{id_}"
            if f.name == "joined_at":
                return f"2020-01-{id_ % 28 + 1:02d}"

        return [[get(f, i) for f in fields] for i in ids]

    def link_companies():
        return list(range(1, n_companies + 1))

    def link_departments(company_ids):
        return [
            [cid * 100 + j for j in range(1, n_depts + 1)]
            for cid in company_ids
        ]

    def link_employees(dept_ids):
        return [
            [did * 100 + j for j in range(1, n_employees + 1)]
            for did in dept_ids
        ]

    def link_profile(emp_ids):
        return [eid * 100 for eid in emp_ids]

    graph = Graph(
        [
            Node(
                "Company",
                [
                    Field("id", Integer, resolve_company),
                    Field("name", String, resolve_company),
                    Field("founded", Integer, resolve_company),
                    Field("revenue", Integer, resolve_company),
                    Link(
                        "departments",
                        Sequence[TypeRef["Department"]],
                        link_departments,
                        requires="id",
                    ),
                ],
            ),
            Node(
                "Department",
                [
                    Field("id", Integer, resolve_department),
                    Field("name", String, resolve_department),
                    Field("budget", Integer, resolve_department),
                    Field("floor", Integer, resolve_department),
                    Link(
                        "employees",
                        Sequence[TypeRef["Employee"]],
                        link_employees,
                        requires="id",
                    ),
                ],
            ),
            Node(
                "Employee",
                [
                    Field("id", Integer, resolve_employee),
                    Field("name", String, resolve_employee),
                    Field("email", String, resolve_employee),
                    Field("role", String, resolve_employee),
                    Field("salary", Integer, resolve_employee),
                    Link(
                        "profile",
                        TypeRef["Profile"],
                        link_profile,
                        requires="id",
                    ),
                ],
            ),
            Node(
                "Profile",
                [
                    Field("id", Integer, resolve_profile),
                    Field("bio", String, resolve_profile),
                    Field("avatar", String, resolve_profile),
                    Field("website", String, resolve_profile),
                    Field("joined_at", String, resolve_profile),
                ],
            ),
            Root(
                [
                    Link(
                        "companies",
                        Sequence[TypeRef["Company"]],
                        link_companies,
                        requires=None,
                    ),
                ]
            ),
        ]
    )
    return graph


def prepare_result(schema, query_str):
    """Run parsing, validation, merging, and execution.

    Returns (graph, proxy_result, merged_query) for benchmarking
    denormalization in isolation.
    """
    graph = schema.graph
    doc = parse_query(query_str)
    op = read_operation(doc, None, None)
    query = op.query

    errors = validate(graph, query)
    assert not errors, errors

    query = QueryMerger(graph).merge(query)

    ctx = create_execution_context(
        query=query,
        query_graph=graph,
        operation=op,
    )
    result = schema.engine.execute(ctx)
    return graph, result, query


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

QUERY_SHALLOW = """
{
    companies {
        name
        founded
    }
}
"""

QUERY_DEEP = """
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
"""

QUERY_DEEP_INLINE_FRAGMENTS = """
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
"""

QUERY_DEEP_NAMED_FRAGMENTS = """
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
"""


# ---------------------------------------------------------------------------
# Fixtures — small dataset (3 × 3 × 5 = 45 leaf entities)
# ---------------------------------------------------------------------------


@pytest.fixture(name="schema_small")
def schema_small_fixture():
    graph = make_graph(n_companies=3, n_depts=3, n_employees=5)
    return Schema(SyncExecutor(), graph)


@pytest.fixture(name="shallow_result")
def shallow_result_fixture(schema_small):
    return prepare_result(schema_small, QUERY_SHALLOW)


@pytest.fixture(name="deep_result")
def deep_result_fixture(schema_small):
    return prepare_result(schema_small, QUERY_DEEP)


@pytest.fixture(name="deep_inline_fragments_result")
def deep_inline_fragments_result_fixture(schema_small):
    return prepare_result(schema_small, QUERY_DEEP_INLINE_FRAGMENTS)


@pytest.fixture(name="deep_named_fragments_result")
def deep_named_fragments_result_fixture(schema_small):
    return prepare_result(schema_small, QUERY_DEEP_NAMED_FRAGMENTS)


# ---------------------------------------------------------------------------
# Fixtures — large dataset (10 × 5 × 10 = 500 leaf entities)
# ---------------------------------------------------------------------------


@pytest.fixture(name="schema_large")
def schema_large_fixture():
    graph = make_graph(n_companies=10, n_depts=5, n_employees=10)
    return Schema(SyncExecutor(), graph)


@pytest.fixture(name="deep_result_large")
def deep_result_large_fixture(schema_large):
    return prepare_result(schema_large, QUERY_DEEP)


# ---------------------------------------------------------------------------
# Benchmarks
# ---------------------------------------------------------------------------


def test_denormalize_shallow(benchmark, shallow_result):
    """1 level: 3 companies, 2 fields each."""
    graph, result, query = shallow_result

    data = benchmark.pedantic(
        lambda: DenormalizeGraphQL(graph, result, "Query").process(query),
        iterations=10,
        rounds=5000,
    )
    assert len(data["companies"]) == 3


def test_denormalize_deep(benchmark, deep_result):
    """4 levels: 3 companies, 9 departments, 45 employees, 45 profiles."""
    graph, result, query = deep_result

    data = benchmark.pedantic(
        lambda: DenormalizeGraphQL(graph, result, "Query").process(query),
        iterations=10,
        rounds=2000,
    )
    companies = data["companies"]
    assert len(companies) == 3
    assert "bio" in companies[0]["departments"][0]["employees"][0]["profile"]


def test_denormalize_deep_inline_fragments(
    benchmark, deep_inline_fragments_result
):
    """4 levels with inline fragments — exercises visit_fragment at each level."""
    graph, result, query = deep_inline_fragments_result

    data = benchmark.pedantic(
        lambda: DenormalizeGraphQL(graph, result, "Query").process(query),
        iterations=10,
        rounds=2000,
    )
    companies = data["companies"]
    assert len(companies) == 3
    assert "bio" in companies[0]["departments"][0]["employees"][0]["profile"]


def test_denormalize_deep_named_fragments(
    benchmark, deep_named_fragments_result
):
    """4 levels with overlapping named fragments."""
    graph, result, query = deep_named_fragments_result

    data = benchmark.pedantic(
        lambda: DenormalizeGraphQL(graph, result, "Query").process(query),
        iterations=10,
        rounds=2000,
    )
    companies = data["companies"]
    assert len(companies) == 3
    emp = companies[0]["departments"][0]["employees"][0]
    assert "email" in emp
    assert "salary" in emp
    assert "joined_at" in emp["profile"]


def test_denormalize_deep_large(benchmark, deep_result_large):
    """4 levels, large dataset: 10 companies, 50 depts, 500 employees, 500 profiles."""
    graph, result, query = deep_result_large

    data = benchmark.pedantic(
        lambda: DenormalizeGraphQL(graph, result, "Query").process(query),
        iterations=5,
        rounds=500,
    )
    companies = data["companies"]
    assert len(companies) == 10
    assert len(companies[0]["departments"]) == 5
    assert len(companies[0]["departments"][0]["employees"]) == 10
