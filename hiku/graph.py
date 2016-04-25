from collections import OrderedDict

from .types import to_instance
from .utils import kw_only


class Option(object):

    def __init__(self, name, type_=None, default=None):
        self.name = name
        self.type = to_instance(type_) if type_ is not None else None
        self.default = default


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

        options, doc = kw_only(kwargs, [], ['options', 'doc'])

        self.name = name
        self.type = to_instance(type_) if type_ is not None else None
        self.func = func
        self.options = OrderedDict((o.name, o) for o in (options or ()))
        self.doc = doc


class Edge(object):

    def __init__(self, name, fields, **kwargs):
        self.name = name
        self.fields = OrderedDict((f.name, f) for f in fields)
        self.doc, = kw_only(kwargs, [], ['doc'])


class Link(object):

    def __init__(self, name, requires, entity, func, **kwargs):
        to_list, options, doc = kw_only(kwargs, ['to_list'], ['options', 'doc'])

        self.name = name
        self.requires = requires
        self.entity = entity
        self.func = func
        self.to_list = to_list
        self.options = OrderedDict((o.name, o) for o in (options or ()))
        self.doc = doc


class Graph(Edge):

    def __init__(self, items):
        super(Graph, self).__init__(None, items)


class link(object):

    @classmethod
    def _decorator(cls, to_list, entity, **kw):
        requires, = kw_only(kw, ['requires'])

        def decorator(func):
            def link_factory(name, **_kw):
                if requires:
                    required_field, = kw_only(_kw, ['requires'])
                else:
                    kw_only(_kw, [])
                    required_field = None
                return Link(name, required_field, entity, func, to_list=to_list)
            return link_factory
        return decorator

    @classmethod
    def one(cls, entity, **kw):
        return cls._decorator(False, entity, **kw)

    @classmethod
    def many(cls, entity, **kw):
        return cls._decorator(True, entity, **kw)
