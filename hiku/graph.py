class Field(object):

    def __init__(self, name, func):
        self.name = name
        self.func = func


class Edge(object):

    def __init__(self, name, fields):
        self.name = name
        self.fields = {f.name: f for f in fields}


class Link(object):

    def __init__(self, name, requires, entity, func, to_list=False):
        self.name = name
        self.requires = requires
        self.entity = entity
        self.func = func
        self.to_list = to_list
