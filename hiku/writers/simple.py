from __future__ import unicode_literals

from ..edn import dumps as _dumps, TaggedElement, List
from ..result import Ref, Result
from ..compat import text_type


def default(obj):
    if isinstance(obj, Ref):
        return TaggedElement('graph/ref', List((obj.node, obj.ident)))
    raise TypeError('Can not tag this object: {!r}'.format(obj))


def _transform(obj):
    if isinstance(obj, list):
        return [_transform(v) for v in obj]
    elif isinstance(obj, dict):
        assert all(isinstance(k, text_type) for k in obj.keys())
        return {k: _transform(v) for k, v in obj.items()}
    elif isinstance(obj, Result):
        return _transform(obj.root)
    else:
        return obj


def _transform_idx(idx):
    for name, value in idx.items():
        yield name, {ident: _transform(val)
                     for ident, val in value.items()}


def dumps(result, ensure_ascii=True):
    data = _transform(result)
    data.update(_transform_idx(result.index))
    return _dumps(data, default=default, ensure_ascii=ensure_ascii)
