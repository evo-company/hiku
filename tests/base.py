import unittest
from contextlib import contextmanager
try:
    from itertools import zip_longest
    from unittest.mock import patch as _patch, Mock as _Mock
    from unittest.mock import call as _call, ANY as _ANY
except ImportError:
    from mock import patch as _patch, Mock as _Mock
    from mock import call as _call, ANY as _ANY
    from itertools import izip_longest as zip_longest

from hiku.refs import Ref
from hiku.types import GenericMeta
from hiku.query import Field, Link, Edge

patch = _patch
Mock = _Mock
call = _call
ANY = _ANY


def _ne(self, other):
    return not self.__eq__(other)


def _eq(self, other):
    if type(self) is not type(other):
        return False
    return self.__dict__ == other.__dict__


def _edge_eq(self, other):
    if type(self) is not type(other):
        return False
    return self.fields_map == dict(other.fields_map)


_field_patch = patch.multiple(Field, __eq__=_eq, __ne__=_ne)
_link_patch = patch.multiple(Link, __eq__=_eq, __ne__=_ne)
_edge_patch = patch.multiple(Edge, __eq__=_edge_eq, __ne__=_ne)


@contextmanager
def reqs_eq_patcher():
    with _field_patch, _link_patch, _edge_patch:
        yield


_ref_patch = patch.multiple(Ref, __eq__=_eq, __ne__=_ne)


@contextmanager
def ref_eq_patcher():
    with _ref_patch:
        yield


_type_patch = patch.multiple(GenericMeta, __eq__=_eq, __ne__=_ne)


@contextmanager
def type_eq_patcher():
    with _type_patch:
        yield


_missing = type('<missing>', (object,), {})


def result_match(result, value, path=None):
    path = [] if path is None else path
    if isinstance(value, dict):
        for k, v in value.items():
            ok, sp, sr, sv = result_match(result[k], v, path + [k])
            if not ok:
                return ok, sp, sr, sv
    elif isinstance(value, (list, tuple)):
        pairs = zip_longest(result, value, fillvalue=_missing)
        for i, (v1, v2) in enumerate(pairs):
            ok, sp, sr, sv = result_match(v1, v2, path + [i])
            if not ok:
                return ok, sp, sr, sv
    elif result != value:
        return False, path, result, value

    return True, None, None, None


def check_result(result, value):
    ok, path, subres, subval = result_match(result, value)
    if not ok:
        path_str = 'result' + ''.join('[{!r}]'.format(v) for v in path)
        msg = ('Result mismatch, first different element '
               'path: {}, value: {!r}, expected: {!r}'
               .format(path_str, subres, subval))
        raise AssertionError(msg)


class TestCase(unittest.TestCase):

    def assertResult(self, result, value):
        check_result(result, value)
