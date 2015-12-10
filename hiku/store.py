from functools import partial
from collections import defaultdict


class Ref(object):

    def __init__(self, storage, entity, ident):
        self.storage = storage
        self.entity = entity
        self.ident = ident

    def __getitem__(self, key):
        return self.storage.index[self.entity].get(self.ident)[key]

    def __repr__(self):
        return '<{}:{}>'.format(self.entity, self.ident)

    def __eq__(self, other):
        return self.storage.index[self.entity].get(self.ident) == other


class Store(object):

    def __init__(self):
        self.refs = {}
        self.index = defaultdict(partial(defaultdict, dict))

    def add(self, values):
        self.index.update(values)

    def update(self, entity, ident, values):
        self.index[entity][ident].update(values)

    def ref(self, entity, ident):
        return Ref(self, entity, ident)
