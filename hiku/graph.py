from collections import OrderedDict

from .types import to_instance


class Field(object):

    def __init__(self, name, *other):
        self.name = name
        if not len(other):
            raise TypeError('Missing required argument')
        elif len(other) == 1:
            self.type = None
            self.func, = other
        elif len(other) == 2:
            type_, self.func = other
            self.type = to_instance(type_)
        else:
            raise TypeError('More positional arguments ({}) than expected (2)'
                            .format(len(other)))


class Edge(object):

    def __init__(self, name, fields):
        self.name = name
        self.fields = OrderedDict((f.name, f) for f in fields)


class Link(object):

    def __init__(self, name, requires, entity, func, to_list=False):
        self.name = name
        self.requires = requires
        self.entity = entity
        self.func = func
        self.to_list = to_list
