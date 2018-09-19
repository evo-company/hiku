from __future__ import unicode_literals

from ..edn import dumps as _dumps, TaggedElement, List
from ..result import Reference, ROOT
from ..compat import text_type


def default(obj):
    if isinstance(obj, Reference):
        return TaggedElement('graph/ref', List((obj.node, obj.ident)))
    raise TypeError('Can not tag this object: {!r}'.format(obj))


def _transform(obj):
    if isinstance(obj, list):
        return [_transform(v) for v in obj]
    elif isinstance(obj, dict):
        assert all(isinstance(k, text_type) for k in obj.keys())
        return {k: _transform(v) for k, v in obj.items()}
    else:
        return obj


def dumps(result, ensure_ascii=True):
    data = _transform(result.__idx__.root)
    for name, value in result.__idx__.items():
        if name != ROOT.node:
            data[name] = {ident: _transform(val)
                          for ident, val in value.items()}
    return _dumps(data, default=default, ensure_ascii=ensure_ascii)
