import pytest
from temboardui.acl import TRN


def test_trn_parse():
    with pytest.raises(Exception) as e:
        TRN.parse("malformed:trn")
    assert str(e.value) == "Malformed TRN"

    trn = TRN.parse("trn:temboard:core:user:alice")

    assert trn.scope == "core"
    assert trn.type == "user"
    assert trn.name == "alice"

    assert str(trn) == "trn:temboard:core:user:alice"

    trn = TRN.parse("trn:temboard:core:instance:prod/pg001.bridoulou.fr")

    assert trn.scope == "core"
    assert trn.type == "instance"
    assert trn.name == "prod/pg001.bridoulou.fr"


def test_trn_parent():
    trn = TRN.parse("trn:temboard:core:user:alice")
    assert str(trn.parent) == "trn:temboard:core:user:*"

    trn = TRN.parse("trn:temboard:core:group:prod/dba")
    assert str(trn.parent) == "trn:temboard:core:group:prod"

    trn = TRN.parse("trn:temboard:core:group:prod/dba/indus")
    assert str(trn.parent) == "trn:temboard:core:group:prod/dba"

    trn = TRN.parse("trn:temboard:*:*:*")
    assert str(trn.parent) == "trn:temboard:*:*:*"


def test_trn_parents():
    trn = TRN.parse("trn:temboard:core:user:alice")
    parents = trn.parents
    assert len(parents) == 5

    assert str(parents[0]) == "trn:temboard:core:user:alice"
    assert str(parents[1]) == "trn:temboard:core:user:*"
    assert str(parents[2]) == "trn:temboard:core:*:*"
    assert str(parents[3]) == "trn:temboard:*:*:*"
    assert str(parents[4]) == "*"
