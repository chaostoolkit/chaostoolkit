# -*- coding: utf-8 -*-
from functools import wraps
import traceback
from typing import Any

from logzero import logger

from chaostoolkit.types import Plan

__all__ = ["Report"]


class Report:
    def with_plan(self, plan: Plan):
        self.title = plan.get("title", "N/A")
        self.description = plan.get("description", "N/A")

    def __enter__(self) -> "Report":
        return self

    def __exit__(self, ex_type: Any, ex_value: Any, tb: Any):
        if ex_value:
            logger.error(ex_value)
