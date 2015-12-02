class Field(object):

    def __init__(self, name, func):
        self.name = name
        self.func = func


class Edge(object):

    def __init__(self, name, fields):
        self.name = name
        self.fields = fields


class Link(object):

    def __init__(self, requires, entity, func):
        self.requires = requires
        self.entity = entity
        self.func = func
