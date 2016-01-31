from __future__ import absolute_import

from json import dumps as _dumps

from ..result import Ref


def default(obj):
    if isinstance(obj, Ref):
        return obj.storage[obj.entity][obj.ident]
    raise TypeError('Can not encode this type: {!r}'.format(obj))


def dumps(result):
    return _dumps(result, default=default)
