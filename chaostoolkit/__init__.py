# -*- coding: utf-8 -*-
from datetime import date, datetime
import decimal
import uuid

__version__ = '1.3.0'
__all__ = ['__version__', 'encoder']


def encoder(o: object) -> str:
    """
    Perform some additional encoding for types JSON doesn't support natively.

    We don't try to respect any ECMA specification here as we want to retain
    as much information as we can.
    """
    if isinstance(o, (date, datetime)):
        # we do not meddle with the timezone and assume the date was stored
        # with the right information of timezone as +-HH:MM
        return o.isoformat()
    elif isinstance(o, decimal.Decimal):
        return str(o)
    elif isinstance(o, uuid.UUID):
        return str(o)

    raise TypeError(
        "Object of type '{}' is not JSON serializable".format(type(o)))
