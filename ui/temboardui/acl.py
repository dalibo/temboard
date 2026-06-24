class MalformedTRN(ValueError):
    pass


class TRN:
    """
    TRN represent a temboard role/resource name.
    It's a kind of path separated by `:`.

    Alice user:
    trn:temboard:core:user:alice

    pg001.bridoulou.fr instance from prod environment:
    trn:temboard:core:instance:prod/pg001.bridoulou.fr:5432
    """

    def __init__(self, scope, type, name):
        self.scope = scope
        self.type = type
        self.name = name

    def __eq__(self, value):
        if isinstance(value, TRN):
            return (self.scope, self.type, self.name) == (
                value.scope,
                value.type,
                value.name,
            )
        return NotImplemented

    def __hash__(self):
        return hash(str(self))

    @classmethod
    def parse(cls, trn):
        if not isinstance(trn, str):
            raise MalformedTRN("TRN must be a string")
        elems = trn.split(":", 4)
        if len(elems) != 5 or elems[0] != "trn" or elems[1] != "temboard":
            raise MalformedTRN("Malformed TRN")
        return cls(elems[2], elems[3], elems[4])

    def __str__(self):
        return f"trn:temboard:{self.scope}:{self.type}:{self.name}"

    @property
    def parent(self):
        parent = TRN(self.scope, self.type, self.name)

        if self.name != "*":
            parent.name = "*"
            if "/" in self.name:
                names = str.split(self.name, "/")
                parent.name = "/".join(names[:-1])
            return parent
        if self.type != "*":
            parent.type = "*"
            return parent
        parent.scope = "*"
        return parent

    @property
    def parents(self):
        trns = []
        trn = self
        while str(trn) != "trn:temboard:*:*:*":
            if trn not in trns:
                trns.append(trn)
            trn = trn.parent
        trns.append(trn)
        trns.append("*")
        return trns
