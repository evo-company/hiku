from contextlib import contextmanager
try:
    from unittest.mock import patch as _patch, Mock as _Mock
    from unittest.mock import call as _call
except ImportError:
    from mock import patch as _patch, Mock as _Mock
    from mock import call as _call

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
