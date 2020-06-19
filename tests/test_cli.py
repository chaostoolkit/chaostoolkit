# -*- coding: utf-8 -*-
from datetime import datetime
from decimal import Decimal
import io
import json
import os
import shutil
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
import yaml

from chaostoolkit.cli import cli, encoder

empty_settings_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'fixtures', 'empty-settings.yaml'))


def test_source_experiment_is_mandatory():
    runner = CliRunner()
    result = runner.invoke(cli, ['run'])
    assert result.exit_code == 2
    assert result.exception
    assert 'Error: Missing argument "SOURCE".' in result.output or \
           'Error: Missing argument \'SOURCE\'.' in result.output


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

    curdir = os.path.normpath(os.path.join(
        os.path.abspath(os.path.dirname(__file__)), '..'))
    subdir = os.path.join(curdir, 'tests', 'fixtures')
    try:
        result = runner.invoke(
            cli, [
                '--settings', empty_settings_path, '--change-dir', subdir,
                'run'])
        assert os.getcwd() == subdir
    finally:
        os.chdir(curdir)
    assert os.getcwd() == curdir


def test_dry(log_file):
    runner = CliRunner()
    exp_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'check-file-exists.json')
    result = runner.invoke(cli, [
        '--settings', empty_settings_path,
        '--log-file', log_file.name, 'run', '--dry', exp_path])
    assert result.exit_code == 0
    assert result.exception is None

    log_file.seek(0)
    log = log_file.read().decode('utf-8')
    assert 'Dry mode enabled' in log


@patch('chaostoolkit.cli.notify', spec=True)
def test_notify_run_complete(notify, log_file):
    testdir = os.path.normpath(os.path.join(
        os.path.abspath(os.path.dirname(__file__)), '..'))
    runner = CliRunner()
    exp_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'check-file-exists.json')
    result = runner.invoke(
        cli, [
            '--settings', empty_settings_path, '--change-dir', testdir,
            'run', exp_path
        ])
    assert result.exit_code == 0
    assert result.exception is None

    notify.assert_any_call(ANY, RunFlowEvent.RunStarted, ANY)
    notify.assert_called_with(ANY, RunFlowEvent.RunCompleted, ANY)


@patch('chaostoolkit.cli.notify', spec=True)
def test_notify_run_failure(notify, log_file):
    runner = CliRunner()
    exp_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'check-file-exists-fail.json')
    result = runner.invoke(
        cli, ['--settings', empty_settings_path, 'run', exp_path])
    assert result.exit_code == 1
    assert result.exception

    notify.assert_any_call(ANY, RunFlowEvent.RunStarted, ANY)
    notify.assert_any_call(ANY, RunFlowEvent.RunFailed, ANY)


@patch('chaostoolkit.cli.notify', spec=True)
def test_notify_run_failure_with_deviation(notify, log_file):
    runner = CliRunner()
    exp_path = os.path.join(
        os.path.dirname(__file__), 'fixtures',
        'check-file-exists-deviated.json')
    dummy_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'dummy.txt')
    settings_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'fake_settings.yaml')

    with open(dummy_path, 'w'):
        result = runner.invoke(
            cli, ['--settings', empty_settings_path, 'run', exp_path])
    assert result.exit_code == 1
    assert result.exception

    notify.assert_any_call(ANY, RunFlowEvent.RunStarted, ANY)
    notify.assert_any_call(ANY, RunFlowEvent.RunFailed, ANY)
    notify.assert_any_call(ANY, RunFlowEvent.RunDeviated, ANY)


@patch('chaostoolkit.cli.notify', spec=True)
def test_notify_validate_complete(notify):
    runner = CliRunner()
    exp_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'check-file-exists.json')
    result = runner.invoke(
        cli, ['--settings', empty_settings_path, 'validate', exp_path])
    assert result.exit_code == 0
    assert result.exception is None

    notify.assert_any_call(ANY, ValidateFlowEvent.ValidateStarted, ANY)
    notify.assert_called_with(ANY, ValidateFlowEvent.ValidateCompleted, ANY)


@patch('chaostoolkit.cli.notify', spec=True)
def test_notify_validate_failure(notify):
    runner = CliRunner()
    exp_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'invalid-plan.json')
    result = runner.invoke(
        cli, ['--settings', empty_settings_path, 'validate', exp_path])
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
            '--settings', empty_settings_path,
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
        '--settings', empty_settings_path,
        'discover', '--no-install', 'chaostoolkit-kubernetes'])
    assert result.exit_code == 0
    assert result.exception is None

    notify.assert_any_call(ANY, DiscoverFlowEvent.DiscoverStarted, ANY)
    notify.assert_called_with(ANY, DiscoverFlowEvent.DiscoverFailed, ANY, err)


@patch('chaostoolkit.cli.notify', spec=True)
def test_notify_init_complete(notify):
    # fill the inputs of the init command
    inputs = '\n'.join([
        'a dummy test',
        'Y',
        'a steady state hypo',
        '1',
        'Y',
        'true',
        'default',
        'N',
        'Y',
        '1',
        'Y',
        'true',
        'default',
        'N',
        'N',
        'N'])
    runner = CliRunner()

    base_path = os.path.dirname(__file__)
    disco_path = os.path.join(base_path, 'fixtures', 'disco.json')
    export_path_json = os.path.join(base_path, 'experiment.json')
    export_path_yaml = os.path.join(base_path, 'experiment.yaml')

    export_paths = [None, export_path_json, export_path_yaml]

    for export_path in export_paths:
        cli_params = ['--settings', empty_settings_path,
                      'init', '--discovery-path', disco_path]

        if export_path:
            cli_params.extend(['--experiment-path', export_path])
        else:
            export_path = os.path.join(os.getcwd(), "experiment.json")

        result = runner.invoke(cli, cli_params, input=inputs)

        assert result.exit_code == 0
        assert result.exception is None
        assert os.path.exists(export_path)

        notify.assert_any_call(ANY, InitFlowEvent.InitStarted)
        notify.assert_any_call(ANY, InitFlowEvent.InitCompleted, ANY)


def test_show_settings():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as d:
        settings_path = os.path.join(d, 'settings.yaml')
        shutil.copy(
            os.path.join(
                os.path.dirname(__file__), 'fixtures',
                'complete-settings.yaml'), settings_path)
        settings_content = open(settings_path).read()
        result = runner.invoke(
            cli, ['--settings', settings_path, 'settings', 'show'])
        assert result.exit_code == 0
        assert result.exception is None
        assert yaml.dump(yaml.load(result.output), canonical=True) == \
            yaml.dump(yaml.load(settings_content), canonical=True)


def test_get_settings_entry_as_yaml():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as d:
        settings_path = os.path.join(d, 'settings.yaml')
        shutil.copy(
            os.path.join(
                os.path.dirname(__file__), 'fixtures',
                'complete-settings.yaml'), settings_path)
        settings_content = open(settings_path).read()
        result = runner.invoke(
            cli,
            [
                '--settings', settings_path, 'settings', 'get',
                'auths.chaos\\\\.example\\\\.com:8443.type'
            ]
        )
        assert result.exit_code == 0
        assert result.exception is None
        assert result.output == "bearer\n...\n\n"


def test_get_settings_entry_as_json():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as d:
        settings_path = os.path.join(d, 'settings.yaml')
        shutil.copy(
            os.path.join(
                os.path.dirname(__file__), 'fixtures',
                'complete-settings.yaml'), settings_path)
        settings_content = open(settings_path).read()
        result = runner.invoke(
            cli,
            [
                '--settings', settings_path, 'settings', 'get',
                '--format=json',
                'auths.chaos\\\\.example\\\\.com:8443.type'
            ]
        )
        assert result.exit_code == 0
        assert result.exception is None
        assert result.output == '"bearer"\n'


def test_get_settings_entry_as_string():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as d:
        settings_path = os.path.join(d, 'settings.yaml')
        shutil.copy(
            os.path.join(
                os.path.dirname(__file__), 'fixtures',
                'complete-settings.yaml'), settings_path)
        settings_content = open(settings_path).read()
        result = runner.invoke(
            cli,
            [
                '--settings', settings_path, 'settings', 'get',
                '--format=string',
                'auths.chaos\\\\.example\\\\.com:8443.type'
            ]
        )
        assert result.exit_code == 0
        assert result.exception is None
        assert result.output == 'bearer\n'


def test_get_settings_not_found_key_exits_with_1():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as d:
        settings_path = os.path.join(d, 'settings.yaml')
        shutil.copy(
            os.path.join(
                os.path.dirname(__file__), 'fixtures',
                'complete-settings.yaml'), settings_path)
        settings_content = open(settings_path).read()
        result = runner.invoke(
            cli,
            [
                '--settings', settings_path, 'settings', 'get',
                'burp'
            ]
        )
        assert result.exit_code == 1


def test_set_settings_not_found_key_exits_with_1():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as d:
        settings_path = os.path.join(d, 'settings.yaml')
        shutil.copy(
            os.path.join(
                os.path.dirname(__file__), 'fixtures',
                'complete-settings.yaml'), settings_path)
        settings_content = open(settings_path).read()
        result = runner.invoke(
            cli,
            [
                '--settings', settings_path, 'settings', 'set',
                'burp', '"hello"'
            ]
        )
        assert result.exit_code == 1


def test_set_settings_entry():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as d:
        settings_path = os.path.join(d, 'settings.yaml')
        shutil.copy(
            os.path.join(
                os.path.dirname(__file__), 'fixtures',
                'complete-settings.yaml'), settings_path)
        settings_content = open(settings_path).read()
        result = runner.invoke(
            cli,
            [
                '--settings', settings_path, 'settings', 'set',
                'auths.chaos\\\\.example\\\\.com:8443', '"basic"'
            ]
        )
        assert result.exit_code == 0
    
        result = runner.invoke(
            cli,
            [
                '--settings', settings_path, 'settings', 'get',
                '--format=json',
                'auths.chaos\\\\.example\\\\.com:8443'
            ]
        )
        assert result.exit_code == 0
        assert result.output == '"basic"\n'


def test_set_settings_entry_as_a_list():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as d:
        settings_path = os.path.join(d, 'settings.yaml')
        shutil.copy(
            os.path.join(
                os.path.dirname(__file__), 'fixtures',
                'complete-settings.yaml'), settings_path)
        settings_content = open(settings_path).read()
        result = runner.invoke(
            cli,
            [
                '--settings', settings_path, 'settings', 'set',
                'auths.chaos\\\\.example\\\\.com:8443', '["basic", "bearer"]'
            ]
        )
        assert result.exit_code == 0
    
        result = runner.invoke(
            cli,
            [
                '--settings', settings_path, 'settings', 'get',
                '--format=json',
                'auths.chaos\\\\.example\\\\.com:8443'
            ]
        )
        assert result.exit_code == 0
        assert json.loads(result.output) == ["basic", "bearer"]


def test_set_settings_entry_as_a_int():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as d:
        settings_path = os.path.join(d, 'settings.yaml')
        shutil.copy(
            os.path.join(
                os.path.dirname(__file__), 'fixtures',
                'complete-settings.yaml'), settings_path)
        settings_content = open(settings_path).read()
        result = runner.invoke(
            cli,
            [
                '--settings', settings_path, 'settings', 'set',
                'auths.chaos\\\\.example\\\\.com:8443', '3'
            ]
        )
        assert result.exit_code == 0
    
        result = runner.invoke(
            cli,
            [
                '--settings', settings_path, 'settings', 'get',
                '--format=json',
                'auths.chaos\\\\.example\\\\.com:8443'
            ]
        )
        assert result.exit_code == 0
        assert json.loads(result.output) == 3


def test_remove_settings_not_found_key_exits_with_1():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as d:
        settings_path = os.path.join(d, 'settings.yaml')
        shutil.copy(
            os.path.join(
                os.path.dirname(__file__), 'fixtures',
                'complete-settings.yaml'), settings_path)
        settings_content = open(settings_path).read()
        result = runner.invoke(
            cli,
            [
                '--settings', settings_path, 'settings', 'remove',
                'burp'
            ]
        )
        assert result.exit_code == 1


def test_remove_settings_entry():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as d:
        settings_path = os.path.join(d, 'settings.yaml')
        shutil.copy(
            os.path.join(
                os.path.dirname(__file__), 'fixtures',
                'complete-settings.yaml'), settings_path)
        settings_content = open(settings_path).read()
        result = runner.invoke(
            cli,
            [
                '--settings', settings_path, 'settings', 'remove',
                'auths.chaos\\\\.example\\\\.com:8443'
            ]
        )
        assert result.exit_code == 0
    
        result = runner.invoke(
            cli,
            [
                '--settings', settings_path, 'settings', 'get',
                '--format=json',
                'auths.chaos\\\\.example\\\\.com:8443'
            ]
        )
        assert result.exit_code == 1
