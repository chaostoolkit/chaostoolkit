# -*- coding: utf-8 -*-
import os

from chaoslib.settings import CHAOSTOOLKIT_CONFIG_PATH
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


def test_default_settings_file(log_file):
    runner = CliRunner()
    exp_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'well-formed-experiment.json')
    result = runner.invoke(cli, [
        '--log-file', log_file.name, 'run', exp_path])
    assert result.exit_code == 1

    log_file.seek(0)
    log = log_file.read().decode('utf-8')
    message = "Using settings file '{}'".format(CHAOSTOOLKIT_CONFIG_PATH)
    assert message in log


def test_specify_settings_file(log_file):
    runner = CliRunner()
    settings_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'fake_settings.yaml')
    exp_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'well-formed-experiment.json')
    result = runner.invoke(cli, [
        '--log-file', log_file.name, '--settings', settings_path, 'run',
        exp_path])
    assert result.exit_code == 1

    log_file.seek(0)
    log = log_file.read().decode('utf-8')
    message = "Using settings file '{}'".format(settings_path)
    assert message in log
