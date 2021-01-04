class HashableDict(dict):
    def __hash__(self):
        return hash((frozenset(self.keys()), frozenset(self.values())))

