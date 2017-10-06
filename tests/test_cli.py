# -*- coding: utf-8 -*-
import click
from click.testing import CliRunner

from chaostoolkit.cli import cli


def test_path_to_experiment_description_is_mandatory():
    runner = CliRunner()
    result = runner.invoke(cli, ['run'])
    assert result.exit_code == 2
    assert result.exception
    assert 'Error: Missing argument "path".' in result.output


def test_path_to_experiment_description_is_mandatory():
    runner = CliRunner()
    result = runner.invoke(cli, ['run', 'invalid.jsn'])
    assert result.exit_code == 2
    assert result.exception
    assert 'Error: Invalid value for "path": Path '\
           '"invalid.jsn" does not exist.' in result.output


def test_path_to_experiment_description_is_mandatory():
    runner = CliRunner()
    result = runner.invoke(cli, ['run', 'invalid.jsn'])
    assert result.exit_code == 2
    assert result.exception
    assert 'Error: Invalid value for "path": Path "invalid.jsn" does not exist.' in result.output
