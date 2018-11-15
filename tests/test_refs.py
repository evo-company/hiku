from hiku.types import Record, Any, TypeRef, Sequence, Optional, Integer
from hiku.types import Callable
from hiku.builder import build, Q
from hiku.expr.core import S, to_expr
from hiku.expr.refs import ref_to_req, RequirementsExtractor
from hiku.expr.refs import type_to_query
from hiku.expr.nodes import Symbol, Tuple
from hiku.expr.checker import check, fn_types

from .base import ref


def check_ref(ref_chain, types, arg_type, query_items):
    ref_ = ref(ref_chain)
    ref_query = type_to_query(arg_type) if arg_type else None
    query = build(query_items)
    assert ref_to_req(types, ref_, ref_query) == query


def check_type(type_, query_items):
    type_query = type_to_query(type_)
    query = build(query_items)
    assert type_query == query


def check_extract(node, types, query_items):
    node_query = RequirementsExtractor.extract(types, node)
    query = build(query_items)
    assert node_query == query


def check_refs(types, expr, query_items):
    ast, functions = to_expr(expr)
    query = build(query_items)
    env = fn_types(functions)
    env.update(types['__root__'].__field_types__)
    ast = check(ast, types, env)
    expr_reqs = RequirementsExtractor.extract(types, ast)
    assert expr_reqs == query


def test_any():
    check_ref([('foo', Any)], {}, None, [Q.foo])


def test_scalar():
    check_ref([('foo', Integer)], {}, None, [Q.foo])


def test_ref_to_record_field():
    check_ref([
        ('bar', Integer),
        ('foo', Record[{'bar': Integer}]),
    ], {}, None, [Q.foo[Q.bar]])


def test_ref_to_record_arg():
    check_ref([
        ('foo', Record[{'bar': Integer}]),
    ], {}, Record[{'bar': Integer}], [Q.foo[Q.bar]])


def test_ref_to_sequence():
    check_ref([
        ('foo', Sequence[Integer]),
    ], {}, None, [Q.foo])


def test_ref_to_sequence_item():
    check_ref([
        (None, Integer),
        ('foo', Sequence[Integer]),
    ], {}, None, [Q.foo])


def test_ref_to_sequence_of_records():
    check_ref([
        ('bar', Integer),
        (None, Record[{'bar': Integer}]),
        ('foo', Sequence[Record[{'bar': Integer}]]),
    ], {}, None, [Q.foo[Q.bar]])


def test_ref_to_typeref():
    check_ref([
        ('bar', Integer),
        (None, TypeRef['Foo']),
        ('foo', Sequence[TypeRef['Foo']]),
    ], {'Foo': Record[{'bar': Integer}]}, None, [Q.foo[Q.bar]])


def test_ref_to_optional():
    check_ref([
        (None, Integer),
        ('bar', Optional[Integer]),
        (None, TypeRef['Foo']),
        ('foo', Optional[TypeRef['Foo']]),
    ], {'Foo': Record[{'bar': Optional[Integer]}]}, None, [Q.foo[Q.bar]])


def test_ref_to_scalar_opt():
    chain = [
        ('bar', Integer, {'arg': 42}),
        ('foo', Record[{'bar': Integer}]),
    ]
    check_ref(chain, {}, None, [Q.foo[Q.bar(arg=42)]])


def test_ref_to_record_opt():
    chain = [
        ('bar', Integer),
        ('foo', Record[{'bar': Integer}], {'arg': 42}),
    ]
    check_ref(chain, {}, None, [Q.foo(arg=42)[Q.bar]])


def test_ref_to_sequence_scalar_opt():
    chain = [
        (None, Integer),
        ('foo', Sequence[Integer], {'arg': 42}),
    ]
    check_ref(chain, {}, None, [Q.foo(arg=42)])


def test_ref_to_sequence_record_opt():
    chain = [
        ('bar', Integer),
        (None, Record[{'bar': Integer}]),
        ('foo', Sequence[Record[{'bar': Integer}]], {'arg': 42}),
    ]
    check_ref(chain, {}, None, [Q.foo(arg=42)[Q.bar]])


def test_query_for_record_with_scalar():
    check_type(Record[{'foo': Integer}], [Q.foo])


def test_query_for_record_with_optional_scalar():
    check_type(Record[{'foo': Optional[Integer]}], [Q.foo])


def test_query_for_record_with_sequence_of_scalar():
    check_type(Record[{'foo': Sequence[Integer]}], [Q.foo])


def test_query_for_record_with_record():
    check_type(Record[{'foo': Record[{'bar': Integer}]}], [Q.foo[Q.bar]])


def test_query_for_record_with_optional_record():
    check_type(Record[{'foo': Optional[Record[{'bar': Integer}]]}],
               [Q.foo[Q.bar]])


def test_query_for_record_with_sequence_of_records():
    check_type(Record[{'foo': Sequence[Record[{'bar': Integer}]]}],
               [Q.foo[Q.bar]])


def test_query_for_sequence_of_records():
    check_type(Sequence[Record[{'foo': Sequence[Record[{'bar': Integer}]]}]],
               [Q.foo[Q.bar]])


def test_query_for_optional_record():
    check_type(Optional[Record[{'foo': Optional[Record[{'bar': Integer}]]}]],
               [Q.foo[Q.bar]])


def test_refs_for_symbol():
    check_refs({'__root__': Record[{'foo': Integer}]}, S.foo, [Q.foo])


def test_extract_symbol():
    node = Symbol('foo')
    node.__ref__ = ref([
        ('foo', Integer),
    ])
    check_extract(node, {}, [Q.foo])


def test_extract_get():
    record_node = Symbol('foo')
    record_node.__ref__ = ref([
        ('foo', TypeRef['Foo']),
    ])
    node = Tuple([Symbol('get'), record_node, Symbol('bar')])
    node.__ref__ = ref([
        ('bar', Integer),
        ('foo', TypeRef['Foo']),
    ])
    check_extract(node, {'Foo': Record[{'bar': Integer}]}, [Q.foo[Q.bar]])


def test_extract_arg_of_scalar_type():
    func_sym = Symbol('func')
    func_sym.__ref__ = ref([
        (func_sym.name, Callable[Integer, ]),
    ])
    arg_sym = Symbol('foo')
    arg_sym.__ref__ = ref([
        (arg_sym.name, Integer),
    ])
    node = Tuple([func_sym, arg_sym])
    check_extract(node, {}, [Q.foo])


def test_extract_arg_of_complex_type():
    func_sym = Symbol('func')
    func_sym.__ref__ = ref([
        (func_sym.name, Callable[Record[{'bar': Integer}], ]),
    ])
    arg_sym = Symbol('foo')
    arg_sym.__ref__ = ref([
        (arg_sym.name, TypeRef['Foo']),
    ])
    node = Tuple([func_sym, arg_sym])
    check_extract(node, {'Foo': Record[{'bar': Integer}]}, [Q.foo[Q.bar]])
