from collections import OrderedDict

from .types import to_instance


def _kw_only(names, kwargs):
    kwargs = kwargs.copy()
    values = [kwargs.pop(name, None) for name in names]
    if kwargs:
        raise TypeError('Unknown keyword arguments: {}'
                        .format(', '.join(kwargs.keys())))
    else:
        return values


class Field(object):

    def __init__(self, name, *other, **kwargs):
        if not len(other):
            raise TypeError('Missing required argument')
        elif len(other) == 1:
            type_, func = None, other[0]
        elif len(other) == 2:
            type_, func = other
        else:
            raise TypeError('More positional arguments ({}) than expected (2)'
                            .format(len(other)))

        doc, = _kw_only(['doc'], kwargs)

        self.name = name
        self.type = to_instance(type_) if type_ is not None else None
        self.func = func
        self.doc = doc


class Edge(object):

    def __init__(self, name, fields, **kwargs):
        self.name = name
        self.fields = OrderedDict((f.name, f) for f in fields)
        self.doc, = _kw_only(['doc'], kwargs)


class Link(object):

    def __init__(self, name, requires, entity, func, to_list=False, **kwargs):
        self.name = name
        self.requires = requires
        self.entity = entity
        self.func = func
        self.to_list = to_list
        self.doc, = _kw_only(['doc'], kwargs)
