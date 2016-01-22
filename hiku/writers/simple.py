from __future__ import unicode_literals

from ..edn import dumps as _dumps, TaggedElement, List, Keyword
from ..store import Ref
from ..compat import text_type


def default(obj):
    if isinstance(obj, Ref):
        return TaggedElement('graph/ref', List((obj.entity, obj.ident)))
    raise TypeError('Can not tag this object: {!r}'.format(obj))


def _transform(obj):
    if isinstance(obj, list):
        return [_transform(v) for v in obj]
    elif isinstance(obj, dict):
        assert all(isinstance(k, text_type) for k in obj.keys())
        return {Keyword(k): _transform(v) for k, v in obj.items()}
    else:
        return obj


def _transform_idx(idx):
    for name, value in idx.items():
        yield Keyword(name), {ident: _transform(val)
                              for ident, val in value.items()}


def dumps(store):
    data = _transform(store)
    data.update(_transform_idx(store.idx))
    return _dumps(data, default=default)
