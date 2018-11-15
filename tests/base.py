from functools import reduce
try:
    from itertools import zip_longest
    from unittest.mock import patch as _patch, Mock as _Mock
    from unittest.mock import call as _call, ANY as _ANY
except ImportError:
    from mock import patch as _patch, Mock as _Mock
    from mock import call as _call, ANY as _ANY
    from itertools import izip_longest as zip_longest

from hiku.expr.refs import Ref, NamedRef

patch = _patch
Mock = _Mock
call = _call
ANY = _ANY


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


def _ref_reducer(backref, item):
    try:
        name, to, options = item
    except ValueError:
        (name, to), options = item, None
    if name is None:
        return Ref(backref, to)
    else:
        return NamedRef(backref, name, to, options=options)


def ref(chain):
    return reduce(_ref_reducer, reversed(chain), None)
