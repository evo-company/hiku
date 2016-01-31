from collections import defaultdict


class Ref(object):

    def __init__(self, storage, entity, ident):
        self.storage = storage
        self.entity = entity
        self.ident = ident

    def __getitem__(self, key):
        return self.storage[self.entity].get(self.ident)[key]

    def __repr__(self):
        return '<{}:{}>'.format(self.entity, self.ident)

    def __eq__(self, other):
        return self.storage[self.entity].get(self.ident) == other


class State(defaultdict):

    def __init__(self):
        super(State, self).__init__(State)


class Result(State):

    def __init__(self):
        super(Result, self).__init__()
        self.idx = State()

    def ref(self, entity, ident):
        return Ref(self.idx, entity, ident)
