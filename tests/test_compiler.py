import difflib

from textwrap import dedent
from collections import OrderedDict

import astor
import pytest

from hiku.types import Optional, String, Record, Any, TypeRef, Sequence
from hiku.graph import Graph, Field, Node, Link, Root
from hiku.compat import PY38
from hiku.expr.core import define, S, if_, each, to_expr, if_some
from hiku.expr.checker import check, fn_types
from hiku.expr.compiler import ExpressionCompiler


@define(Any, _name="foo")
def foo(value):
    pass


@define(Any, _name="bar")
def bar(value):
    pass


@define(Any, Record[{"c": Any}], _name="baz")
def baz(a, y):
    pass


def noop(*_):
    return 1 / 0


# TODO: refactor
ENV = Graph(
    [
        Node(
            "x",
            [
                Field("b", None, noop),
            ],
        ),
        Node(
            "y",
            [
                Field("c", None, noop),
                Link("x1", TypeRef["x"], noop, requires=None),
                Link("xs", Sequence[TypeRef["x"]], noop, requires=None),
            ],
        ),
        Root(
            [
                Field("a", None, noop),
                Field("nitrox", Optional[String], noop),
                Link("x", TypeRef["x"], noop, requires=None),
                Link("y", TypeRef["y"], noop, requires=None),
                Link("y1", TypeRef["y"], noop, requires=None),
                Link("ys", Sequence[TypeRef["y"]], noop, requires=None),
            ]
        ),
    ]
)


def check_compiles(dsl_expr, code):
    types = ENV.__types__

    expr, functions = to_expr(dsl_expr)
    env = fn_types(functions)
    env.update(types["__root__"].__field_types__)

    expr = check(expr, types, env)

    # test eval
    lambda_expr = ExpressionCompiler.compile_lambda_expr(expr)
    eval(compile(lambda_expr, "<expr>", "eval"))

    # test compile
    py_expr = ExpressionCompiler.compile_expr(expr)

    first = astor.to_source(py_expr).strip()
    second = dedent(code).strip()
    if first != second:
        msg = "Compiled code is not equal:\n\n{}".format(
            "\n".join(difflib.ndiff(first.splitlines(), second.splitlines()))
        )
        raise AssertionError(msg)


def test_tuple():
    check_compiles(
        foo(S.a),
        """
        env['foo'](ctx['a'])
        """,
    )


def test_get_expr():
    check_compiles(
        foo(S.x.b),
        """
        env['foo'](ctx['x']['b'])
        """,
    )


def test_if_expr():
    check_compiles(
        if_(1, foo(S.a), bar(S.a)),
        """
        (env['foo'](ctx['a']) if 1 else env['bar'](ctx['a']))
        """,
    )
    check_compiles(
        if_(1, foo(S.a), "nothing"),
        """
        (env['foo'](ctx['a']) if 1 else 'nothing')
        """,
    )


def test_if_some_expr():
    check_compiles(
        if_some([S.x, S.nitrox], S.x, "nothing"),
        "next(x if x is not None else 'nothing' for x in (ctx['nitrox'],)) ",
    )


def test_each_expr():
    check_compiles(
        each(S.i, S.ys, baz(S.a, S.i)),
        """
        [env['baz'](ctx['a'], i) for i in ctx['ys']]
        """,
    )


def test_name_collision():
    check_compiles(
        each(S.i, S.ys, each(S.i, S.i.xs, bar(S.i.b))),
        """
        [[env['bar'](i_2['b']) for i_2 in i['xs']] for i in ctx['ys']]
        """,
    )


def test_list():
    check_compiles(
        [foo(1), bar(2)],
        """
        [env['foo'](1), env['bar'](2)]
        """,
    )


def test_dict():
    check_compiles(
        OrderedDict([("foo-value", foo(1)), ("bar-value", bar(2))]),
        """
        {'foo-value': env['foo'](1), 'bar-value': env['bar'](2)}
        """,
    )


def test_generic_none():
    check_compiles(None, "None")


@pytest.mark.skipif(not PY38, reason="Python < 3.8")
def test_generic_bool():
    check_compiles(True, "(True)")


def test_generic_long():
    expected = "18446744073709551616"
    check_compiles(2**64, "({})".format(expected))


def test_generic_float():
    check_compiles(1.1, "(1.1)")
