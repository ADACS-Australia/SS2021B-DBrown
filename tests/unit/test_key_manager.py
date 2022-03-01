import sys
from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock

import pytest

from finorch.config.config import api_config_manager
from scripts.finorch_key_manager import set_ssh_key, remove_ssh_key


def call_argv(fn, argv):
    orig_args = sys.argv
    orig_stdout = sys.stdout

    try:
        with NamedTemporaryFile() as f:
            sys.argv = argv
            sys.stdout = open(f.name, 'w')
            fn()
    finally:
        sys.stdout = orig_stdout
        sys.argv = orig_args


def test_set_ssh_key_session_name():
    with pytest.raises(SystemExit) as ex:
        call_argv(set_ssh_key, [sys.argv[0], 'notarealsession'])

    assert ex.value.code == 1


def test_set_ssh_key_session_map():
    with pytest.raises(SystemExit) as ex:
        call_argv(set_ssh_key, [sys.argv[0], 'local'])

    assert ex.value.code == 1


def test_set_ssh_key_args_len():
    with pytest.raises(SystemExit) as ex:
        call_argv(set_ssh_key, [sys.argv[0], 'ozstar'])

    assert ex.value.code == 1

    with pytest.raises(SystemExit) as ex:
        call_argv(set_ssh_key, [sys.argv[0], 'ozstar', 'something', 'somethingelse'])

    assert ex.value.code == 1

    with pytest.raises(SystemExit) as ex:
        call_argv(set_ssh_key, [sys.argv[0], 'ssh'])

    assert ex.value.code == 1

    with pytest.raises(SystemExit) as ex:
        call_argv(set_ssh_key, [sys.argv[0], 'ssh', 'something'])

    assert ex.value.code == 1

    with pytest.raises(SystemExit) as ex:
        call_argv(set_ssh_key, [sys.argv[0], 'ssh', 'something', 'b', 'c'])

    assert ex.value.code == 1


def test_set_ssh_key_generic():
    with NamedTemporaryFile() as temp_file:
        with open(temp_file.name, 'w') as f:
            f.write('my cool key')

        api_config_manager.set = MagicMock()

        with pytest.raises(SystemExit) as ex:
            call_argv(set_ssh_key, [sys.argv[0], 'ssh', 'my.host.name', temp_file.name])

        assert ex.value.code == 0

        assert api_config_manager.set.call_count == 1
        assert api_config_manager.set.call_args[0][0] == 'ssh'
        assert api_config_manager.set.call_args[0][1] == 'my.host.name'
        assert api_config_manager.set.call_args[0][2] == 'my cool key'


def test_set_ssh_key_not_generic():
    with NamedTemporaryFile() as temp_file:
        with open(temp_file.name, 'w') as f:
            f.write('my cool key')

        api_config_manager.set = MagicMock()

        with pytest.raises(SystemExit) as ex:
            call_argv(set_ssh_key, [sys.argv[0], 'ozstar', temp_file.name])

        assert ex.value.code == 0

        assert api_config_manager.set.call_count == 1
        assert api_config_manager.set.call_args[0][0] == 'ozstar'
        assert api_config_manager.set.call_args[0][1] == 'key'
        assert api_config_manager.set.call_args[0][2] == 'my cool key'


def test_set_ssh_key_not_generic_key_not_exists():
    api_config_manager.set = MagicMock()

    with pytest.raises(SystemExit) as ex:
        call_argv(set_ssh_key, [sys.argv[0], 'ozstar', 'not_a_real_path'])

    assert ex.value.code == 1


def test_remove_ssh_key_session_name():
    with pytest.raises(SystemExit) as ex:
        call_argv(remove_ssh_key, [sys.argv[0], 'notarealsession'])

    assert ex.value.code == 1


def test_remove_ssh_key_session_map():
    with pytest.raises(SystemExit) as ex:
        call_argv(remove_ssh_key, [sys.argv[0], 'local'])

    assert ex.value.code == 1


def test_remove_ssh_key_args_len():
    with pytest.raises(SystemExit) as ex:
        call_argv(remove_ssh_key, [sys.argv[0], 'ozstar', 'blah'])

    assert ex.value.code == 1

    with pytest.raises(SystemExit) as ex:
        call_argv(remove_ssh_key, [sys.argv[0], 'ssh'])

    assert ex.value.code == 1

    with pytest.raises(SystemExit) as ex:
        call_argv(remove_ssh_key, [sys.argv[0], 'ssh', 'something', 'b'])

    assert ex.value.code == 1


def test_remove_ssh_key_generic():
    api_config_manager.set = MagicMock()

    with pytest.raises(SystemExit) as ex:
        call_argv(remove_ssh_key, [sys.argv[0], 'ssh', 'my.host.name'])

    assert ex.value.code == 0

    assert api_config_manager.set.call_count == 1
    assert api_config_manager.set.call_args[0][0] == 'ssh'
    assert api_config_manager.set.call_args[0][1] == 'my.host.name'
    assert api_config_manager.set.call_args[0][2] == ''


def test_remove_ssh_key_not_generic():
    api_config_manager.set = MagicMock()

    with pytest.raises(SystemExit) as ex:
        call_argv(remove_ssh_key, [sys.argv[0], 'ozstar'])

    assert ex.value.code == 0

    assert api_config_manager.set.call_count == 1
    assert api_config_manager.set.call_args[0][0] == 'ozstar'
    assert api_config_manager.set.call_args[0][1] == 'key'
    assert api_config_manager.set.call_args[0][2] == ''
