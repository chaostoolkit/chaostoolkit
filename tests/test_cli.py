# -*- coding: utf-8 -*-
from datetime import datetime
from decimal import Decimal
import json
import os
import sys
import tempfile
from unittest.mock import ANY, patch
import uuid

from chaoslib.exceptions import DiscoveryFailed
from chaoslib.notification import DiscoverFlowEvent, InitFlowEvent, \
    RunFlowEvent, ValidateFlowEvent
from chaoslib.settings import CHAOSTOOLKIT_CONFIG_PATH
import click
from click.testing import CliRunner
import pytest

from chaostoolkit.cli import cli, encoder


def test_source_experiment_is_mandatory():
    runner = CliRunner()
    result = runner.invoke(cli, ['run'])
    assert result.exit_code == 2
    assert result.exception
    assert 'Error: Missing argument "source".' in result.output


def test_source_path_must_exist(log_file):
    runner = CliRunner()
    result = runner.invoke(cli, [
        '--log-file', log_file.name, 'run', 'invalid.jsn'])
    assert result.exit_code == 1
    assert result.exception

    log_file.seek(0)
    log = log_file.read().decode('utf-8')
    assert 'Path "invalid.jsn" does not exist.' in log


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


def test_json_encoder_failure():
    class Dummy:
        pass

    with pytest.raises(TypeError) as x:
        encoder(Dummy())


def test_json_encoder_datetime():
    now = datetime.utcnow()
    assert encoder(now) == now.isoformat()


def test_json_encoder_decimal():
    d = Decimal('1.38')
    assert encoder(d) == '1.38'


def test_json_encoder_uuid():
    u = uuid.uuid4()
    assert encoder(u) == str(u)


def test_change_directory(log_file):
    runner = CliRunner()

    curdir = os.getcwd()
    try:
        result = runner.invoke(cli, ['--change-dir', '/tmp', 'run'])
        assert os.getcwd() == '/tmp'
    finally:
        os.chdir(curdir)
    assert os.getcwd() == curdir


def test_dry(log_file):
    runner = CliRunner()
    exp_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'check-file-exists.json')
    result = runner.invoke(cli, [
        '--log-file', log_file.name, 'run', '--dry', exp_path])
    assert result.exit_code == 0
    assert result.exception is None

    log_file.seek(0)
    log = log_file.read().decode('utf-8')
    assert 'Dry mode enabled' in log


@patch('chaostoolkit.cli.notify', spec=True)
def test_notify_run_complete(notify, log_file):
    runner = CliRunner()
    exp_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'check-file-exists.json')
    result = runner.invoke(cli, ['run', exp_path])
    assert result.exit_code == 0
    assert result.exception is None

    notify.assert_any_call(ANY, RunFlowEvent.RunStarted, ANY)
    notify.assert_called_with(ANY, RunFlowEvent.RunCompleted, ANY)


@patch('chaostoolkit.cli.notify', spec=True)
def test_notify_run_failure(notify, log_file):
    runner = CliRunner()
    exp_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'check-file-exists-fail.json')
    result = runner.invoke(cli, ['run', exp_path])
    assert result.exit_code == 1
    assert result.exception

    notify.assert_any_call(ANY, RunFlowEvent.RunStarted, ANY)
    notify.assert_called_with(ANY, RunFlowEvent.RunFailed, ANY)


@patch('chaostoolkit.cli.notify', spec=True)
def test_notify_validate_complete(notify):
    runner = CliRunner()
    exp_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'check-file-exists.json')
    result = runner.invoke(cli, ['validate', exp_path])
    assert result.exit_code == 0
    assert result.exception is None

    notify.assert_any_call(ANY, ValidateFlowEvent.ValidateStarted, ANY)
    notify.assert_called_with(ANY, ValidateFlowEvent.ValidateCompleted, ANY)


@patch('chaostoolkit.cli.notify', spec=True)
def test_notify_validate_failure(notify):
    runner = CliRunner()
    exp_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'invalid-plan.json')
    result = runner.invoke(cli, ['validate', exp_path])
    assert result.exit_code == 1
    assert result.exception

    notify.assert_any_call(ANY, ValidateFlowEvent.ValidateStarted, ANY)
    notify.assert_called_with(ANY, ValidateFlowEvent.ValidateFailed, ANY, ANY)


@patch('chaostoolkit.cli.notify', spec=True)
@patch('chaostoolkit.cli.disco', spec=True)
def test_notify_discover_failure(disco, notify):
    with tempfile.NamedTemporaryFile() as f:
        discovered = {'msg': 'hello'}
        disco.return_value = discovered

        runner = CliRunner()
        result = runner.invoke(cli, [
            'discover', '--discovery-path', f.name,
            '--no-install', 'chaostoolkit-kubernetes'])
        assert result.exit_code == 0
        assert result.exception is None

        notify.assert_any_call(ANY, DiscoverFlowEvent.DiscoverStarted, ANY)
        notify.assert_called_with(
            ANY, DiscoverFlowEvent.DiscoverCompleted, discovered)

        f.seek(0)
        data = f.read()
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        assert json.loads(data) == discovered


@patch('chaostoolkit.cli.notify', spec=True)
@patch('chaostoolkit.cli.disco', spec=True)
def test_notify_discover_complete(disco, notify):
    err = DiscoveryFailed()
    disco.side_effect = err

    runner = CliRunner()
    result = runner.invoke(cli, [
        'discover', '--no-install', 'chaostoolkit-kubernetes'])
    assert result.exit_code == 0
    assert result.exception is None

    notify.assert_any_call(ANY, DiscoverFlowEvent.DiscoverStarted, ANY)
    notify.assert_called_with(ANY, DiscoverFlowEvent.DiscoverFailed, ANY, err)
