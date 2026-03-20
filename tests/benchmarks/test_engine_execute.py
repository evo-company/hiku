"""Benchmark engine execution with a realistic multi-node, multi-level graph.

Measures the hiku execution pipeline overhead (InitOptions, SplitQuery,
GroupQuery, field/link scheduling, result indexing) at varying query depths
and data volumes — from a shallow 1-level query to a full 4-level traversal.

Graph topology:
    Root -> Company -> Department -> Employee -> Profile

Resolvers return deterministic fake data so we measure framework overhead,
not resolver cost.
"""

import pytest

from hiku.executors.sync import SyncExecutor
from hiku.extensions.query_parse_cache import QueryParserCache
from hiku.extensions.query_validation_cache import QueryValidationCache
from hiku.graph import Field, Graph, Link, Node, Root
from hiku.schema import Schema
from hiku.types import Integer, Sequence, String, TypeRef


# ---------------------------------------------------------------------------
# Data dimensions
# ---------------------------------------------------------------------------

N_COMPANIES = 3
N_DEPTS_PER_COMPANY = 3
N_EMPLOYEES_PER_DEPT = 5


# ---------------------------------------------------------------------------
# Resolvers — minimal work, deterministic output
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Link functions
# ---------------------------------------------------------------------------

def link_companies():
    return list(range(1, N_COMPANIES + 1))


def link_departments(company_ids):
    return [
        [cid * 10 + j for j in range(1, N_DEPTS_PER_COMPANY + 1)]
        for cid in company_ids
    ]


def link_employees(dept_ids):
    return [
        [did * 10 + j for j in range(1, N_EMPLOYEES_PER_DEPT + 1)]
        for did in dept_ids
    ]


def link_profile(emp_ids):
    return [eid * 10 for eid in emp_ids]


# ---------------------------------------------------------------------------
# Graph fixture
# ---------------------------------------------------------------------------

@pytest.fixture(name="graph")
def graph_fixture():
    return Graph([
        Node("Company", [
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
        ]),
        Node("Department", [
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
        ]),
        Node("Employee", [
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
        ]),
        Node("Profile", [
            Field("id", Integer, resolve_profile),
            Field("bio", String, resolve_profile),
            Field("avatar", String, resolve_profile),
            Field("website", String, resolve_profile),
            Field("joined_at", String, resolve_profile),
        ]),
        Root([
            Link(
                "companies",
                Sequence[TypeRef["Company"]],
                link_companies,
                requires=None,
            ),
        ]),
    ])


@pytest.fixture(name="schema")
def schema_fixture(graph):
    return Schema(SyncExecutor(), graph)


@pytest.fixture(name="schema_cached")
def schema_cached_fixture(graph):
    return Schema(
        SyncExecutor(),
        graph,
        extensions=[
            QueryParserCache(2),
            QueryValidationCache(2),
        ],
    )


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

QUERY_MEDIUM = """
{
    companies {
        name
        departments {
            name
            budget
        }
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

QUERY_WIDE = """
{
    companies {
        id
        name
        founded
        revenue
        departments {
            id
            name
            budget
            floor
        }
    }
}
"""

# Inline fragments at every nesting level — the merger must expand each
# fragment and merge overlapping fields back into the parent node.
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

# Named fragments with deliberate overlap — "Basic" and "Full" fragments
# share fields (e.g. `name`) that the merger must deduplicate, and both
# reference the same nested link forcing link-level merging as well.
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
# Benchmarks
# ---------------------------------------------------------------------------

def test_engine_execute_shallow(benchmark, schema):
    """1 level: root -> companies (2 fields, 3 items)."""
    result = benchmark.pedantic(
        schema.execute_sync,
        args=(QUERY_SHALLOW,),
        iterations=5,
        rounds=1000,
    )
    assert result.errors is None
    assert len(result.data["companies"]) == N_COMPANIES


def test_engine_execute_medium(benchmark, schema):
    """2 levels: root -> companies -> departments (9 departments)."""
    result = benchmark.pedantic(
        schema.execute_sync,
        args=(QUERY_MEDIUM,),
        iterations=5,
        rounds=1000,
    )
    assert result.errors is None
    companies = result.data["companies"]
    assert len(companies) == N_COMPANIES
    assert len(companies[0]["departments"]) == N_DEPTS_PER_COMPANY


def test_engine_execute_deep(benchmark, schema):
    """4 levels: root -> companies -> departments -> employees -> profile.

    Total entities: 3 companies, 9 departments, 45 employees, 45 profiles.
    """
    result = benchmark.pedantic(
        schema.execute_sync,
        args=(QUERY_DEEP,),
        iterations=5,
        rounds=500,
    )
    assert result.errors is None
    companies = result.data["companies"]
    assert len(companies) == N_COMPANIES
    dept = companies[0]["departments"][0]
    assert len(dept["employees"]) == N_EMPLOYEES_PER_DEPT
    assert "bio" in dept["employees"][0]["profile"]


def test_engine_execute_wide(benchmark, schema):
    """2 levels with all fields at each level (8 fields total)."""
    result = benchmark.pedantic(
        schema.execute_sync,
        args=(QUERY_WIDE,),
        iterations=5,
        rounds=1000,
    )
    assert result.errors is None
    companies = result.data["companies"]
    assert len(companies) == N_COMPANIES
    assert "id" in companies[0]
    assert "revenue" in companies[0]
    assert len(companies[0]["departments"]) == N_DEPTS_PER_COMPANY


def test_engine_execute_deep_cached(benchmark, schema_cached):
    """4-level deep query with parser + validation caches enabled."""
    result = benchmark.pedantic(
        schema_cached.execute_sync,
        args=(QUERY_DEEP,),
        iterations=5,
        rounds=500,
    )
    assert result.errors is None
    companies = result.data["companies"]
    assert len(companies) == N_COMPANIES
    dept = companies[0]["departments"][0]
    assert len(dept["employees"]) == N_EMPLOYEES_PER_DEPT


def test_engine_execute_deep_inline_fragments(benchmark, schema):
    """4-level deep query with inline fragments at every level.

    Exercises QueryMerger expanding inline fragments and merging
    overlapping fields back into parent nodes.
    """
    result = benchmark.pedantic(
        schema.execute_sync,
        args=(QUERY_DEEP_INLINE_FRAGMENTS,),
        iterations=5,
        rounds=500,
    )
    assert result.errors is None
    companies = result.data["companies"]
    assert len(companies) == N_COMPANIES
    assert "revenue" in companies[0]
    dept = companies[0]["departments"][0]
    assert len(dept["employees"]) == N_EMPLOYEES_PER_DEPT
    assert "bio" in dept["employees"][0]["profile"]


def test_engine_execute_deep_named_fragments(benchmark, schema):
    """4-level deep query with overlapping named fragments.

    Exercises QueryMerger deduplicating fields that appear in multiple
    fragments (e.g. `name` in both Basic and Full) and merging links
    referenced from separate fragments into a single traversal.
    """
    result = benchmark.pedantic(
        schema.execute_sync,
        args=(QUERY_DEEP_NAMED_FRAGMENTS,),
        iterations=5,
        rounds=500,
    )
    assert result.errors is None
    companies = result.data["companies"]
    assert len(companies) == N_COMPANIES
    assert "founded" in companies[0]
    assert "revenue" in companies[0]
    dept = companies[0]["departments"][0]
    assert "budget" in dept
    assert "floor" in dept
    assert len(dept["employees"]) == N_EMPLOYEES_PER_DEPT
    emp = dept["employees"][0]
    assert "email" in emp
    assert "salary" in emp
    assert "avatar" in emp["profile"]
    assert "joined_at" in emp["profile"]
