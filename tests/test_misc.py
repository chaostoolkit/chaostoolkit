# -*- coding: utf-8 -*-
import pytest
from chaostoolkit.cli import is_yaml


def test_is_yaml():
    assert not is_yaml("experiment.json")
    assert not is_yaml("experiment.JsOn")
    assert is_yaml("experiment.yaml")
    assert is_yaml("experiment.yml")
    assert is_yaml("ExperiMent.YAML")
