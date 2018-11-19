import pytest

from hiku.types import Integer, Record, Optional, TypeRef, Sequence, String
from hiku.expr.core import S, to_expr, if_some, define, each, opt
from hiku.expr.checker import check, fn_types

from .base import ref


def check_ref(node, chain):
    ref_ = ref(chain)
    assert node.__ref__ == ref_


def check_expr(types, expr):
    ast, functions = to_expr(expr)
    env = fn_types(functions)
    env.update(types['__root__'].__field_types__)
    return check(ast, types, env)


def test_get_simple():
    types = {
        'Bar': Record[{'baz': Integer}],
        'Foo': Record[{'bar': TypeRef['Bar']}],
        '__root__': Record[{'foo': TypeRef['Foo']}],
    }
    ast = check_expr(types, S.foo.bar.baz)
    check_ref(ast, [
        ('baz', Integer),
        ('bar', TypeRef['Bar']),
        ('foo', TypeRef['Foo']),
    ])


def test_each_sequence_of_scalar():
    types = {
        '__root__': Record[{'foo': Sequence[Integer]}],
    }
    ast = check_expr(types, each(S.x, S.foo, S.x))
    _, x1, _, x2 = ast.values
    ref_chain = [
        (None, Integer),
        ('foo', Sequence[Integer]),
    ]
    check_ref(x1, ref_chain)
    check_ref(x2, ref_chain)


def test_each_sequence_of_record():
    types = {
        'Bar': Record[{'baz': Integer}],
        'Foo': Record[{'bar': TypeRef['Bar']}],
        '__root__': Record[{'foo': Sequence[TypeRef['Foo']]}],
    }
    ast = check_expr(types, each(S.x, S.foo, S.x.bar.baz))
    _, _, _, x_bar_baz = ast.values
    check_ref(x_bar_baz, [
        ('baz', Integer),
        ('bar', TypeRef['Bar']),
        (None, TypeRef['Foo']),
        ('foo', Sequence[TypeRef['Foo']]),
    ])


def test_if_some_optional():
    types = {
        'Bar': Record[{'baz': Integer}],
        'Foo': Record[{'bar': Sequence[TypeRef['Bar']]}],
        '__root__': Record[{'foo': Optional[TypeRef['Foo']]}],
    }
    ast = check_expr(types, if_some([S.x, S.foo],
                                    each(S.y, S.x.bar,
                                         S.y.baz), None))
    _, _, each_ast, _ = ast.values
    _, _, _, y_baz = each_ast.values
    check_ref(y_baz, [
        ('baz', Integer),
        (None, TypeRef['Bar']),
        ('bar', Sequence[TypeRef['Bar']]),
        (None, TypeRef['Foo']),
        ('foo', Optional[TypeRef['Foo']]),
    ])


def test_opt():
    types = {
        '__root__': Record[{'foo': String}],
    }
    check_ref(
        check_expr(types, opt(S.foo, {})),
        [('foo', String, {})],
    )

    ast = check_expr(types, opt(S.foo, {'option': 42}))
    check_ref(
        ast,
        [('foo', String, {'option': 42})],
    )
    assert ast.values[1].name == 'foo'
    assert ast.values[1].__ref__ is None, ast.values[1].__ref__

    with pytest.raises(TypeError) as err:
        check_expr(types, opt(S.foo, {'option': 42}, 123))
    err.match('More arguments than expected')


def test_optional_args():
    types = {
        'Foo': Record[{'bar': Integer}],
        '__root__': Record[{'foo': Optional[TypeRef['Foo']]}],
    }

    @define(Optional[Record[{'bar': Integer}]])
    def requires_bar(_):
        pass

    @define(Optional[Record[{'baz': Integer}]])
    def requires_unknown(_):
        pass

    check_expr(types, requires_bar(S.foo))
    with pytest.raises(TypeError) as err:
        check_expr(types, requires_unknown(S.foo))
    err.match('Missing field "baz"')


def test_unknown_symbol():
    types = {
        '__root__': Record[{'foo': Integer}],
    }
    check_expr(types, S.foo)
    with pytest.raises(TypeError) as err:
        check_expr(types, S.bar)
    err.match('Unknown symbol "bar"')


def test_missing_field():
    types = {
        '__root__': Record[{'foo': Record[{'bar': Integer}]}],
    }
    check_expr(types, S.foo)
    check_expr(types, S.foo.bar)
    with pytest.raises(TypeError) as err:
        check_expr(types, S.foo.baz)
    err.match('Missing field "baz"')
