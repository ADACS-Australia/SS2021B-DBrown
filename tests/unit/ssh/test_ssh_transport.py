import sys
import uuid
import xmlrpc.client
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from threading import Thread
from time import sleep
from unittest import mock

import pytest

from finorch.client.client import start_client
from finorch.sessions import OzStarSession, SshSession
from finorch.transport.exceptions import TransportConnectionException, TransportGetJobFileException, \
    TransportGetJobFileListException, TransportGetJobStatusException, TransportTerminateException
from finorch.transport.ssh import SshTransport
from finorch.utils.job_status import JobStatus
from tests.unit.local.test_local_client import SCRIPT


def test_constructor():
    with mock.patch('paramiko.SSHClient', autospec=True):  # Test non generic ssh session
        args = {
            'host': 'test.host',
            'username': 'test_username',
            'python_path': '/test/python/path/python',
            'callsign': 'test_callsign'
        }

        t = SshTransport(
            OzStarSession.__new__(OzStarSession),
            '/tmp/exec_path/',
            **args
        )

        assert t._ssh_transport is None
        assert t._ssh_session is None
        assert t._host == args['host']
        assert t._username == args['username']
        assert t._ssh_password is None
        assert t._python_path == args['python_path']
        assert t._env_file is None
        assert t._callsign == args['callsign']
        assert t._ssh_port == 22
        assert t._remote_port is None
        assert t._is_generic is False
        assert t._ssh_client.set_missing_host_key_policy.called

        # Test generic session
        args = {
            'host': 'test.host',
            'username': 'test_username',
            'python_path': '/test/python/path/python',
            'callsign': 'test_callsign',
            'password': 'test_ssh_password',
            'env_file': '/my/test/env_file',
            'ssh_port': 1234
        }

        t = SshTransport(
            SshSession.__new__(SshSession),
            '/tmp/exec_path/',
            **args
        )

        assert t._ssh_transport is None
        assert t._ssh_session is None
        assert t._host == args['host']
        assert t._username == args['username']
        assert t._ssh_password == args['password']
        assert t._python_path == args['python_path']
        assert t._env_file == args['env_file']
        assert t._callsign == args['callsign']
        assert t._ssh_port == args['ssh_port']
        assert t._remote_port is None
        assert t._is_generic is True
        assert t._ssh_client.set_missing_host_key_policy.called


def test_terminate_exception():
    with mock.patch('paramiko.SSHClient', autospec=True):  # Test non generic ssh session
        args = {
            'host': 'test.host',
            'username': 'test_username',
            'python_path': '/test/python/path/python',
            'callsign': 'test_callsign'
        }

        t = SshTransport(
            OzStarSession.__new__(OzStarSession),
            '/tmp/exec_path/',
            **args
        )

        with pytest.raises(TransportTerminateException):
            t.terminate()


def test_connect_key_no_section():
    # Test generic session
    args = {
        'host': 'test.host',
        'username': 'test_username',
        'python_path': '/test/python/path/python',
        'callsign': 'test_callsign'
    }

    with mock.patch('paramiko.SSHClient', autospec=True), \
            mock.patch('finorch.transport.ssh.api_config_manager') as api_config:
        # Test non generic ssh session
        t = SshTransport(
            SshSession.__new__(SshSession),
            '/tmp/exec_path/',
            **args
        )

        api_config.get_section.return_value = None
        with pytest.raises(TransportConnectionException):
            t.connect(remote_port=None)


def test_connect_key_no_key():
    # Test generic session
    args = {
        'host': 'test.host',
        'username': 'test_username',
        'python_path': '/test/python/path/python',
        'callsign': 'test_callsign'
    }

    with mock.patch('paramiko.SSHClient', autospec=True), \
            mock.patch('finorch.transport.ssh.api_config_manager') as api_config:
        # Test non generic ssh session
        t = SshTransport(
            SshSession.__new__(SshSession),
            '/tmp/exec_path/',
            **args
        )

        section_mock = mock.Mock()
        api_config.get_section.return_value = section_mock
        section_mock.get.return_value = None
        with pytest.raises(TransportConnectionException):
            t.connect(remote_port=None)


def transport_mock(t, stdout, stderr):
    transport_mock = mock.Mock()
    t._ssh_client.get_transport.return_value = transport_mock

    session_mock = mock.Mock()
    transport_mock.open_channel.return_value = session_mock

    recv_ready_count = 2

    def recv_ready():
        nonlocal recv_ready_count
        recv_ready_count -= 1
        return recv_ready_count != 0

    session_mock.recv_ready.side_effect = recv_ready
    session_mock.recv.return_value = stdout.encode('utf-8')

    recv_stderr_ready_count = 2

    def recv_stderr_ready():
        nonlocal recv_stderr_ready_count
        recv_stderr_ready_count -= 1
        return recv_stderr_ready_count != 0

    session_mock.recv_stderr_ready.side_effect = recv_stderr_ready
    session_mock.recv_stderr.return_value = stderr.encode('utf-8')

    return session_mock


def test_connect_key_exit_status_ready_error():
    # Test generic session
    args = {
        'host': 'test.host',
        'username': 'test_username',
        'python_path': '/test/python/path/python',
        'callsign': 'test_callsign'
    }

    with mock.patch('paramiko.SSHClient', autospec=True), \
            mock.patch('finorch.transport.ssh.api_config_manager') as api_config, \
            mock.patch('paramiko.RSAKey.from_private_key') as rsa_key:
        # Test non generic ssh session
        t = SshTransport(
            SshSession.__new__(SshSession),
            '/tmp/exec_path/',
            **args
        )

        section_mock = mock.Mock()
        api_config.get_section.return_value = section_mock
        section_mock.get.return_value = 'test_skey'
        rsa_key.return_value = 'test_pkey'

        session_mock = transport_mock(t, "1234\n=EOF=\n", "")
        session_mock.exit_status_ready.return_value = True
        session_mock.exit_status = 1

        with pytest.raises(TransportConnectionException):
            t.connect(remote_port=None)


def test_connect_key_error():
    # Test generic session
    args = {
        'host': 'test.host',
        'username': 'test_username',
        'python_path': '/test/python/path/python',
        'callsign': 'test_callsign'
    }

    with mock.patch('paramiko.SSHClient', autospec=True), \
            mock.patch('finorch.transport.ssh.api_config_manager') as api_config, \
            mock.patch('paramiko.RSAKey.from_private_key') as rsa_key:
        # Test non generic ssh session
        t = SshTransport(
            SshSession.__new__(SshSession),
            '/tmp/exec_path/',
            **args
        )

        section_mock = mock.Mock()
        api_config.get_section.return_value = section_mock
        section_mock.get.return_value = 'test_skey'
        rsa_key.return_value = 'test_pkey'

        session_mock = transport_mock(t, "error\nsomething broke\n=EOF=\n", "")
        session_mock.exit_status_ready.return_value = False

        with pytest.raises(TransportConnectionException):
            t.connect(remote_port=None)

        assert session_mock.close.called


def test_connect_key_bad_port():
    # Test generic session
    args = {
        'host': 'test.host',
        'username': 'test_username',
        'python_path': '/test/python/path/python',
        'callsign': 'test_callsign'
    }

    with mock.patch('paramiko.SSHClient', autospec=True), \
            mock.patch('finorch.transport.ssh.api_config_manager') as api_config, \
            mock.patch('paramiko.RSAKey.from_private_key') as rsa_key:
        # Test non generic ssh session
        t = SshTransport(
            SshSession.__new__(SshSession),
            '/tmp/exec_path/',
            **args
        )

        section_mock = mock.Mock()
        api_config.get_section.return_value = section_mock
        section_mock.get.return_value = 'test_skey'
        rsa_key.return_value = 'test_pkey'

        session_mock = transport_mock(t, "not_a_valid_port\n=EOF=\n", "")
        session_mock.exit_status_ready.return_value = False

        with pytest.raises(TransportConnectionException):
            t.connect(remote_port=None)

        assert session_mock.close.called


def test_connect_key_success_no_env():
    exc, stdout, stderr, orig_stdout, orig_stderr = None, None, None, None, None

    def start_client_thread(argv):
        nonlocal exc, stdout, stderr, orig_stdout, orig_stderr
        exc = None

        # Save argv and output fds
        orig_args = sys.argv
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr

        with NamedTemporaryFile() as out, NamedTemporaryFile() as err:
            stdout = out.name
            stderr = err.name

            sys.stdout = open(out.name, 'w')
            sys.stderr = open(err.name, 'w')

            try:
                sys.argv = argv
                start_client()
            except Exception as e:
                exc = e
            finally:
                # Make sure output is flushed
                sys.stdout.flush()
                sys.stderr.flush()

                # Restore argv and output fds
                sys.argv = orig_args
                sys.stdout = orig_stdout
                sys.stderr = orig_stderr

    t = Thread(target=start_client_thread, args=([None, 'local'],))
    t.start()

    # Wait for the session to start
    sleep(0.5)

    # Make sure output is flushed
    sys.stdout.flush()
    sys.stderr.flush()

    # Read the stdout and stderr files
    out = open(stdout, 'r').read()
    err = open(stderr, 'r').read()

    # Stderr should be empty (no errors)
    assert not err

    lines = out.splitlines()

    # First line should be the port the client is running on
    assert int(lines[0])
    port = int(lines[0])

    # Test generic session
    args = {
        'host': 'test.host',
        'username': 'test_username',
        'python_path': '/test/python/path/python',
        'callsign': 'test_callsign'
    }

    with mock.patch('paramiko.SSHClient', autospec=True), \
            mock.patch('finorch.transport.ssh.api_config_manager') as api_config, \
            mock.patch('paramiko.RSAKey.from_private_key') as rsa_key:
        # Test non generic ssh session
        t = SshTransport(
            SshSession.__new__(SshSession),
            '/tmp/exec_path/',
            **args
        )

        section_mock = mock.Mock()
        api_config.get_section.return_value = section_mock
        section_mock.get.return_value = 'test_skey'
        rsa_key.return_value = 'test_pkey'

        session_mock = transport_mock(t, f"{port}\n=EOF=\n", "")
        session_mock.exit_status_ready.return_value = False
        t._port = port
        t._forward_tunnel = mock.MagicMock()

        assert t.connect(remote_port=None) == port

        assert t._forward_tunnel.called
        assert session_mock.exit_status_ready.called
        assert session_mock.recv_stderr.called
        assert session_mock.recv_stderr_ready.called
        assert session_mock.recv.called
        assert session_mock.recv_ready.called

        command = "bash --login -c \"mkdir -p /tmp/exec_path/ && cd /tmp/exec_path/ && "
        command += f"{args['python_path']} -m finorch.client.client {args['callsign']}\""
        assert session_mock.exec_command.mock_calls[0].args[0] == command

        assert t._ssh_client.connect.mock_calls[0].kwargs == \
               {
                   'hostname': args['host'],
                   'port': 22,
                   'username': args['username'],
                   'pkey': 'test_pkey'
               }

        assert t._connected

        t.terminate()

        assert not t._connected


def test_connect_key_success_with_env():
    exc, stdout, stderr, orig_stdout, orig_stderr = None, None, None, None, None

    def start_client_thread(argv):
        nonlocal exc, stdout, stderr, orig_stdout, orig_stderr
        exc = None

        # Save argv and output fds
        orig_args = sys.argv
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr

        with NamedTemporaryFile() as out, NamedTemporaryFile() as err:
            stdout = out.name
            stderr = err.name

            sys.stdout = open(out.name, 'w')
            sys.stderr = open(err.name, 'w')

            try:
                sys.argv = argv
                start_client()
            except Exception as e:
                exc = e
            finally:
                # Make sure output is flushed
                sys.stdout.flush()
                sys.stderr.flush()

                # Restore argv and output fds
                sys.argv = orig_args
                sys.stdout = orig_stdout
                sys.stderr = orig_stderr

    t = Thread(target=start_client_thread, args=([None, 'local'],))
    t.start()

    # Wait for the session to start
    sleep(0.5)

    # Make sure output is flushed
    sys.stdout.flush()
    sys.stderr.flush()

    # Read the stdout and stderr files
    out = open(stdout, 'r').read()
    err = open(stderr, 'r').read()

    # Stderr should be empty (no errors)
    assert not err

    lines = out.splitlines()

    # First line should be the port the client is running on
    assert int(lines[0])
    port = int(lines[0])

    # Test generic session
    args = {
        'host': 'test.host',
        'username': 'test_username',
        'python_path': '/test/python/path/python',
        'callsign': 'test_callsign',
        'env_file': '/test/env/file'
    }

    with mock.patch('paramiko.SSHClient', autospec=True), \
            mock.patch('finorch.transport.ssh.api_config_manager') as api_config, \
            mock.patch('paramiko.RSAKey.from_private_key') as rsa_key:
        # Test non generic ssh session
        t = SshTransport(
            SshSession.__new__(SshSession),
            '/tmp/exec_path/',
            **args
        )

        section_mock = mock.Mock()
        api_config.get_section.return_value = section_mock
        section_mock.get.return_value = 'test_skey'
        rsa_key.return_value = 'test_pkey'

        session_mock = transport_mock(t, f"{port}\n=EOF=\n", "")
        session_mock.exit_status_ready.return_value = False
        t._port = port
        t._forward_tunnel = mock.MagicMock()

        assert t.connect(remote_port=None) == port

        assert t._forward_tunnel.called
        assert session_mock.exit_status_ready.called
        assert session_mock.recv_stderr.called
        assert session_mock.recv_stderr_ready.called
        assert session_mock.recv.called
        assert session_mock.recv_ready.called

        command = "bash --login -c \"mkdir -p /tmp/exec_path/ && cd /tmp/exec_path/ && "
        command += f"source {args['env_file']} && "
        command += f"{args['python_path']} -m finorch.client.client {args['callsign']}\""
        assert session_mock.exec_command.mock_calls[0].args[0] == command

        assert t._ssh_client.connect.mock_calls[0].kwargs == \
               {
                   'hostname': args['host'],
                   'port': 22,
                   'username': args['username'],
                   'pkey': 'test_pkey'
               }

        assert t._connected

        t.terminate()

        assert not t._connected


def test_connect_password_success_no_env():
    exc, stdout, stderr, orig_stdout, orig_stderr = None, None, None, None, None

    def start_client_thread(argv):
        nonlocal exc, stdout, stderr, orig_stdout, orig_stderr
        exc = None

        # Save argv and output fds
        orig_args = sys.argv
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr

        with NamedTemporaryFile() as out, NamedTemporaryFile() as err:
            stdout = out.name
            stderr = err.name

            sys.stdout = open(out.name, 'w')
            sys.stderr = open(err.name, 'w')

            try:
                sys.argv = argv
                start_client()
            except Exception as e:
                exc = e
            finally:
                # Make sure output is flushed
                sys.stdout.flush()
                sys.stderr.flush()

                # Restore argv and output fds
                sys.argv = orig_args
                sys.stdout = orig_stdout
                sys.stderr = orig_stderr

    t = Thread(target=start_client_thread, args=([None, 'local'],))
    t.start()

    # Wait for the session to start
    sleep(0.5)

    # Make sure output is flushed
    sys.stdout.flush()
    sys.stderr.flush()

    # Read the stdout and stderr files
    out = open(stdout, 'r').read()
    err = open(stderr, 'r').read()

    # Stderr should be empty (no errors)
    assert not err

    lines = out.splitlines()

    # First line should be the port the client is running on
    assert int(lines[0])
    port = int(lines[0])

    # Test generic session
    args = {
        'host': 'test.host',
        'username': 'test_username',
        'password': 'test_password',
        'python_path': '/test/python/path/python',
        'callsign': 'test_callsign'
    }

    with mock.patch('paramiko.SSHClient', autospec=True), \
            mock.patch('finorch.transport.ssh.api_config_manager') as api_config, \
            mock.patch('paramiko.RSAKey.from_private_key') as rsa_key:
        # Test non generic ssh session
        t = SshTransport(
            SshSession.__new__(SshSession),
            '/tmp/exec_path/',
            **args
        )

        section_mock = mock.Mock()
        api_config.get_section.return_value = section_mock
        section_mock.get.return_value = 'test_skey'
        rsa_key.return_value = 'test_pkey'

        session_mock = transport_mock(t, f"{port}\n=EOF=\n", "")
        session_mock.exit_status_ready.return_value = False
        t._port = port
        t._forward_tunnel = mock.MagicMock()

        assert t.connect(remote_port=None) == port

        assert t._forward_tunnel.called
        assert session_mock.exit_status_ready.called
        assert session_mock.recv_stderr.called
        assert session_mock.recv_stderr_ready.called
        assert session_mock.recv.called
        assert session_mock.recv_ready.called

        command = "bash --login -c \"mkdir -p /tmp/exec_path/ && cd /tmp/exec_path/ && "
        command += f"{args['python_path']} -m finorch.client.client {args['callsign']}\""
        assert session_mock.exec_command.mock_calls[0].args[0] == command

        assert t._ssh_client.connect.mock_calls[0].kwargs == \
               {
                   'hostname': args['host'],
                   'port': 22,
                   'username': args['username'],
                   'password': args['password']
               }

        assert t._connected

        t.terminate()

        assert not t._connected


def test_connect_key_success_with_env_remote_port_invalid():
    exc, stdout, stderr, orig_stdout, orig_stderr = None, None, None, None, None

    def start_client_thread(argv):
        nonlocal exc, stdout, stderr, orig_stdout, orig_stderr
        exc = None

        # Save argv and output fds
        orig_args = sys.argv
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr

        with NamedTemporaryFile() as out, NamedTemporaryFile() as err:
            stdout = out.name
            stderr = err.name

            sys.stdout = open(out.name, 'w')
            sys.stderr = open(err.name, 'w')

            try:
                sys.argv = argv
                start_client()
            except Exception as e:
                exc = e
            finally:
                # Make sure output is flushed
                sys.stdout.flush()
                sys.stderr.flush()

                # Restore argv and output fds
                sys.argv = orig_args
                sys.stdout = orig_stdout
                sys.stderr = orig_stderr

    t = Thread(target=start_client_thread, args=([None, 'local'],))
    t.start()

    # Wait for the session to start
    sleep(0.5)

    # Make sure output is flushed
    sys.stdout.flush()
    sys.stderr.flush()

    # Read the stdout and stderr files
    out = open(stdout, 'r').read()
    err = open(stderr, 'r').read()

    # Stderr should be empty (no errors)
    assert not err

    lines = out.splitlines()

    # First line should be the port the client is running on
    assert int(lines[0])
    port = int(lines[0])

    # Test generic session
    args = {
        'host': 'test.host',
        'username': 'test_username',
        'python_path': '/test/python/path/python',
        'callsign': 'test_callsign',
        'env_file': '/test/env/file'
    }

    with mock.patch('paramiko.SSHClient', autospec=True), \
            mock.patch('finorch.transport.ssh.api_config_manager') as api_config, \
            mock.patch('paramiko.RSAKey.from_private_key') as rsa_key:
        # Test non generic ssh session
        t = SshTransport(
            SshSession.__new__(SshSession),
            '/tmp/exec_path/',
            **args
        )

        section_mock = mock.Mock()
        api_config.get_section.return_value = section_mock
        section_mock.get.return_value = 'test_skey'
        rsa_key.return_value = 'test_pkey'

        session_mock = transport_mock(t, f"{port}\n=EOF=\n", "")
        session_mock.exit_status_ready.return_value = False
        t._port = port
        t._forward_tunnel = mock.MagicMock()
        t._connection = mock.MagicMock()

        assert t.connect(remote_port=port+1) == port

        t.terminate()

        assert t._forward_tunnel.called
        assert session_mock.exit_status_ready.called
        assert session_mock.recv_stderr.called
        assert session_mock.recv_stderr_ready.called
        assert session_mock.recv.called
        assert session_mock.recv_ready.called

        command = "bash --login -c \"mkdir -p /tmp/exec_path/ && cd /tmp/exec_path/ && "
        command += f"source {args['env_file']} && "
        command += f"{args['python_path']} -m finorch.client.client {args['callsign']}\""
        assert session_mock.exec_command.mock_calls[0].args[0] == command

        assert t._ssh_client.connect.mock_calls[0].kwargs == \
               {
                   'hostname': args['host'],
                   'port': 22,
                   'username': args['username'],
                   'pkey': 'test_pkey'
               }

        assert t._connection.server_close.called
        assert not t._connected


def test_connect_key_success_with_env_remote_port_valid():
    exc, stdout, stderr, orig_stdout, orig_stderr = None, None, None, None, None

    def start_client_thread(argv):
        nonlocal exc, stdout, stderr, orig_stdout, orig_stderr
        exc = None

        # Save argv and output fds
        orig_args = sys.argv
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr

        with NamedTemporaryFile() as out, NamedTemporaryFile() as err:
            stdout = out.name
            stderr = err.name

            sys.stdout = open(out.name, 'w')
            sys.stderr = open(err.name, 'w')

            try:
                sys.argv = argv
                start_client()
            except Exception as e:
                exc = e
            finally:
                # Make sure output is flushed
                sys.stdout.flush()
                sys.stderr.flush()

                # Restore argv and output fds
                sys.argv = orig_args
                sys.stdout = orig_stdout
                sys.stderr = orig_stderr

    t = Thread(target=start_client_thread, args=([None, 'local'],))
    t.start()

    # Wait for the session to start
    sleep(0.5)

    # Make sure output is flushed
    sys.stdout.flush()
    sys.stderr.flush()

    # Read the stdout and stderr files
    out = open(stdout, 'r').read()
    err = open(stderr, 'r').read()

    # Stderr should be empty (no errors)
    assert not err

    lines = out.splitlines()

    # First line should be the port the client is running on
    assert int(lines[0])
    port = int(lines[0])

    # Connect the client rpc and configure the database
    client_rpc = xmlrpc.client.ServerProxy(
        f'http://localhost:{port}/rpc',
        allow_none=True,
        use_builtin_types=True
    )

    client_rpc.set_exec_path(None)

    # Test generic session
    args = {
        'host': 'test.host',
        'username': 'test_username',
        'python_path': '/test/python/path/python',
        'callsign': 'test_callsign',
        'env_file': '/test/env/file'
    }

    with mock.patch('paramiko.SSHClient', autospec=True), \
            mock.patch('finorch.transport.ssh.api_config_manager') as api_config, \
            mock.patch('paramiko.RSAKey.from_private_key') as rsa_key:
        # Test non generic ssh session
        t = SshTransport(
            SshSession.__new__(SshSession),
            '/tmp/exec_path/',
            **args
        )

        section_mock = mock.Mock()
        api_config.get_section.return_value = section_mock
        section_mock.get.return_value = 'test_skey'
        rsa_key.return_value = 'test_pkey'

        t._port = port
        t._forward_tunnel = mock.MagicMock()

        assert t.connect(remote_port=port) == port

        assert t._forward_tunnel.called

        assert t._ssh_client.connect.mock_calls[0].kwargs == \
               {
                   'hostname': args['host'],
                   'port': 22,
                   'username': args['username'],
                   'pkey': 'test_pkey'
               }

        assert t._connected

        t.terminate()

        assert not t._connected


def test_disconnect():
    # Test generic session
    args = {
        'host': 'test.host',
        'username': 'test_username',
        'python_path': '/test/python/path/python',
        'callsign': 'test_callsign',
        'env_file': '/test/env/file'
    }

    # Test non generic ssh session
    t = SshTransport(
        SshSession.__new__(SshSession),
        '/tmp/exec_path/',
        **args
    )

    t._connection = mock.MagicMock()
    t._ssh_client = mock.MagicMock()

    # Test that we can't disconnect a disconnected session
    with pytest.raises(TransportConnectionException):
        t.disconnect()

    assert not t._connected
    assert not t._ssh_client.close.called
    assert not t._connection.shutdown.called

    # Pretend that the transport is connected
    t._connected = True

    t.disconnect()

    assert not t._connected
    assert t._ssh_client.close.called
    assert t._connection.shutdown.called


def setup_client():
    exc, stdout, stderr, orig_stdout, orig_stderr = None, None, None, None, None

    def start_client_thread(argv):
        nonlocal exc, stdout, stderr, orig_stdout, orig_stderr
        exc = None

        # Save argv and output fds
        orig_args = sys.argv
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr

        with NamedTemporaryFile() as out, NamedTemporaryFile() as err:
            stdout = out.name
            stderr = err.name

            sys.stdout = open(out.name, 'w')
            sys.stderr = open(err.name, 'w')

            try:
                sys.argv = argv
                start_client()
            except Exception as e:
                exc = e
            finally:
                # Make sure output is flushed
                sys.stdout.flush()
                sys.stderr.flush()

                # Restore argv and output fds
                sys.argv = orig_args
                sys.stdout = orig_stdout
                sys.stderr = orig_stderr

    t = Thread(target=start_client_thread, args=([None, 'local'],))
    t.start()

    # Wait for the session to start
    sleep(0.5)

    # Make sure output is flushed
    sys.stdout.flush()
    sys.stderr.flush()

    # Read the stdout and stderr files
    out = open(stdout, 'r').read()
    err = open(stderr, 'r').read()

    # Stderr should be empty (no errors)
    assert not err

    lines = out.splitlines()

    # First line should be the port the client is running on
    assert int(lines[0])
    port = int(lines[0])

    # Test generic session
    args = {
        'host': 'test.host',
        'username': 'test_username',
        'password': 'test_password',
        'python_path': '/test/python/path/python',
        'callsign': 'test_callsign'
    }

    with mock.patch('paramiko.SSHClient', autospec=True), \
            mock.patch('finorch.transport.ssh.api_config_manager') as api_config, \
            mock.patch('paramiko.RSAKey.from_private_key') as rsa_key:
        # Test non generic ssh session
        t = SshTransport(
            SshSession.__new__(SshSession),
            '/tmp/exec_path/',
            **args
        )

        section_mock = mock.Mock()
        api_config.get_section.return_value = section_mock
        section_mock.get.return_value = 'test_skey'
        rsa_key.return_value = 'test_pkey'

        session_mock = transport_mock(t, f"{port}\n=EOF=\n", "")
        session_mock.exit_status_ready.return_value = False
        t._port = port
        t._forward_tunnel = mock.MagicMock()

        assert t.connect(remote_port=None) == port

        return t


def test_start_job():
    client = setup_client()
    with TemporaryDirectory() as tmpdir:
        client._client_rpc.set_exec_path(tmpdir)

        identifier = str(uuid.uuid4())
        with pytest.raises(TransportGetJobStatusException):
            client.get_job_status(identifier)

        identifier = client.start_job(SCRIPT)

        # Test for a valid UUID
        try:
            uuid.UUID(identifier, version=4)
        except ValueError:
            assert False

        while client.get_job_status(identifier) != JobStatus.COMPLETED:
            sleep(0.1)

        assert (Path(tmpdir) / identifier / 'script.k').exists()
        assert (Path(tmpdir) / identifier / 'out.log').exists()
        assert (Path(tmpdir) / identifier / 'out.err').exists()
        assert (Path(tmpdir) / identifier / 'data.pickle').exists()

        assert open(str((Path(tmpdir) / identifier / 'script.k')), 'r').read() == SCRIPT

    client.terminate()


def test_get_jobs():
    client = setup_client()
    with TemporaryDirectory() as tmpdir:
        client._client_rpc.set_exec_path(tmpdir)

        identifier1 = client.start_job(SCRIPT)
        identifier2 = client.start_job(SCRIPT)

        while client.get_job_status(identifier1) != JobStatus.COMPLETED:
            sleep(0.1)

        while client.get_job_status(identifier2) != JobStatus.COMPLETED:
            sleep(0.1)

        jobs = client.get_jobs()
        assert jobs[0]['id'] == 1
        assert jobs[0]['identifier'] == identifier1
        assert jobs[0]['status'] == JobStatus.COMPLETED
        assert 'start_time' in jobs[0]

        assert jobs[1]['id'] == 2
        assert jobs[1]['identifier'] == identifier2
        assert jobs[1]['status'] == JobStatus.COMPLETED
        assert 'start_time' in jobs[1]

    client.terminate()


def test_get_job_file():
    client = setup_client()
    with TemporaryDirectory() as tmpdir:
        client._client_rpc.set_exec_path(tmpdir)

        identifier = client.start_job(SCRIPT)

        while client.get_job_status(identifier) != JobStatus.COMPLETED:
            sleep(0.1)

        with pytest.raises(TransportGetJobFileException):
            client.get_job_file(identifier, 'notreal')

        assert client.get_job_file(identifier, 'script.k').decode('utf-8') == SCRIPT

    client.terminate()


def test_get_job_file_list():
    client = setup_client()
    with TemporaryDirectory() as tmpdir:
        client._client_rpc.set_exec_path(tmpdir)

        identifier = client.start_job(SCRIPT)

        while client.get_job_status(identifier) != JobStatus.COMPLETED:
            sleep(0.1)

        tmp_identifier = str(uuid.uuid4())
        with pytest.raises(TransportGetJobFileListException):
            client.get_job_file_list(tmp_identifier)

        file_list = client.get_job_file_list(identifier)

        for file in ['wrapper.ini', 'data.pickle', 'out.log', 'out.err']:
            found = False
            for f in file_list:
                if f[0] == file:
                    found = True
                    break

            if not found:
                assert False

    client.terminate()


def test_stop_job():
    client = setup_client()
    with TemporaryDirectory() as tmpdir:
        client._client_rpc.set_exec_path(tmpdir)

        identifier = client.start_job(SCRIPT)

        # Not implemented error with LocalClient
        with pytest.raises(xmlrpc.client.Fault):
            client.stop_job(identifier)

    client.terminate()
