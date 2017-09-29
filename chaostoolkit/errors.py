# -*- coding: utf-8 -*-

__all__ = ["UnknownProbe", "UnknownAction", "InvalidPlan", "InvalidProbe",
           "FailedProbe"]


class UnknownProbe(LookupError):
    def __init__(self, name: str):
        LookupError.__init__(
            self, "probe '{name}' is not implemented".format(name=name))


class UnknownAction(LookupError):
    def __init__(self, name: str):
        LookupError.__init__(
            self, "action '{name}' is not implemented".format(name=name))


class InvalidPlan(BaseException):
    pass


class InvalidProbe(BaseException):
    pass


class FailedProbe(BaseException):
    pass
