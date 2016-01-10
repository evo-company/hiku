from ..edn import dumps as _dumps, TaggedElement, Dict, List, Keyword
from ..store import Ref
from ..compat import texttype


def default(obj):
    if isinstance(obj, Ref):
        return TaggedElement('graph/ref', List((obj.entity, obj.ident)))
    elif isinstance(obj, dict):
        return Dict(
            (Keyword(k) if isinstance(k, texttype) else k, v)
            for k, v in obj.items()
        )
    elif isinstance(obj, list):
        return List(obj)
    raise TypeError('Can not tag this object: {!r}'.format(obj))


def dumps(data):
    return _dumps(data, default=default)
