import logging

from flask import abort

logger = logging.getLogger(__name__)


class TRN:
    """
    TRN represent a temboard role/ressource name.
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
        return str(self) == str(value)

    def __hash__(self):
        return hash(str(self))

    @classmethod
    def parse(cls, trn):
        elems = str.split(trn, ":")
        if len(elems) < 5:
            raise Exception("Malformed TRN")
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


class ACLResult:
    def __init__(self, role, action, resource, decision="allowed", statements=None):
        self.role = role
        self.action = action
        self.resource = resource
        self.decision = decision
        self.statements = statements or []

    def raise_for_decision(self):
        log_prefix = "Access <%s %s on %s> "
        log_args = (self.role, self.action, self.resource or "*")

        if self.decision == "allowed":
            logger.debug(
                log_prefix + "allowed by %s",
                *log_args,
                ", ".join(repr(s) for s in self.statements),
            )
            return True
        else:
            if self.decision == "implicitDeny":
                logger.debug(log_prefix + "implicitly denied.", *log_args)
            else:
                logger.debug(
                    log_prefix + "denied by %s",
                    *log_args,
                    ", ".join(repr(s) for s in self.statements if s.deny),
                )
        raise abort(403)


def expand_actions(action):
    """Returns the list of pattern relevant for this action."""
    actions = ["*"]
    if action != "*":
        method, _, endpoint = action.partition(":")
        if method != "*":
            actions.append("*:" + endpoint)
        elif endpoint != "*":
            actions.append(method + ":*")
        actions.append(action)
    return actions
