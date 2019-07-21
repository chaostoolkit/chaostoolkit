# -*- coding: utf-8 -*-
from datetime import date, datetime
import decimal
import json
import uuid

import pytest

from chaostoolkit.cli import encoder


def test_encode_date_and_datetime():
    now = datetime.now()
    utcnow = datetime.utcnow()
    today = datetime.today()

    d = {"now": now, "utcnow": utcnow, "today": today}
    
    doc = json.dumps(d, default=encoder)

    assert now.isoformat() in doc
    assert utcnow.isoformat() in doc
    assert today.isoformat() in doc


def test_encode_uuid():
    u = uuid.uuid4()

    doc = json.dumps({"u": u}, default=encoder)
    assert str(u) in doc


def test_encode_decimal():
    d = decimal.Decimal("6.7")

    doc = json.dumps({"d": d}, default=encoder)
    assert str(d) in doc


def test_unknown_type():
    class Dummy:
        pass

    with pytest.raises(TypeError) as x:
        json.dumps({"d": Dummy()})
    assert "not JSON serializable" in str(x.value)
