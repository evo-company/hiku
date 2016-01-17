import unittest
from contextlib import contextmanager
try:
    from itertools import zip_longest
    from unittest.mock import patch as _patch, Mock as _Mock
    from unittest.mock import call as _call
except ImportError:
    from mock import patch as _patch, Mock as _Mock
    from mock import call as _call
    from itertools import izip_longest as zip_longest

from hiku.query import Field, Link, Edge


patch = _patch
Mock = _Mock
call = _call


def _ne(self, other):
    return not self.__eq__(other)


def _req_eq(self, other):
    if type(self) is not type(other):
        return False
    return self.__dict__ == other.__dict__


_field_patch = patch.multiple(Field, __eq__=_req_eq, __ne__=_ne)
_link_patch = patch.multiple(Link, __eq__=_req_eq, __ne__=_ne)
_edge_patch = patch.multiple(Edge, __eq__=_req_eq, __ne__=_ne)


@contextmanager
def reqs_eq_patcher():
    with _field_patch, _link_patch, _edge_patch:
        yield


def store_match(store, value, path=None):
    path = [] if path is None else path
    if isinstance(value, dict):
        for k, v in value.items():
            ok, sp, sv = store_match(store[k], v, path + [k])
            if not ok:
                return ok, sp, sv
    elif isinstance(value, (list, tuple)):
        pairs = zip_longest(store, value)
        for i, (v1, v2) in enumerate(pairs):
            ok, sp, sv = store_match(v1, v2, path + [i])
            if not ok:
                return ok, sp, sv
    elif store != value:
        return False, path, value

    return True, None, None


class TestCase(unittest.TestCase):

    def assertResult(self, store, value):
        ok, path, subval = store_match(store, value)
        if not ok:
            path_str = 'store' + ''.join('[{!r}]'.format(v) for v in path)
            msg = ('Result mismatch, first different element '
                   'path: {}, value: {!r}'
                   .format(path_str, subval))
            raise self.failureException(msg)
