import logging
import sys
import xmlrpc.client
from tempfile import NamedTemporaryFile
from threading import Thread
from time import sleep

from finorch.client.client import start_client, prepare_log_file, run
from finorch.config.config import client_config_manager


def test_start_client():
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

    for argv in [[None], [None, 'notreal', 'notreal']]:
        t = Thread(target=start_client_thread, args=(argv,))
        t.start()
        t.join()

        assert exc
        assert str(exc) == 'Incorrect number of parameters'

    t = Thread(target=start_client_thread, args=([None, 'notreal'],))
    t.start()
    t.join()

    assert exc
    assert str(exc) == 'Session type notreal does not exist.'

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

    # Second line should be the magic terminator
    assert lines[1] == '=EOF='

    # Terminate the client
    client_rpc = xmlrpc.client.ServerProxy(
        f'http://localhost:{port}/rpc',
        allow_none=True,
        use_builtin_types=True
    )

    client_rpc.terminate()

    t.join()


def test_prepare_log_file():
    # Delete the client log file
    (client_config_manager.get_log_directory() / 'client.log').unlink(missing_ok=True)

    prepare_log_file()

    logging.info("Test Log Entry")

    with open(client_config_manager.get_log_directory() / 'client.log', 'r') as f:
        assert f.readline().split('-')[-1].strip() == "Test Log Entry"


def test_run():
    exc, stdout, stderr, orig_stdout, orig_stderr = None, None, None, None, None

    def run_thread(argv):
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
                run()
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

    for argv in [[None], [None, 'notreal', 'notreal']]:
        # Wipe the log file
        (client_config_manager.get_log_directory() / 'client.log').unlink(missing_ok=True)

        t = Thread(target=run_thread, args=(argv,))
        t.start()
        t.join()

        # Should be no exception as it's caught internally
        assert not exc

        with open(client_config_manager.get_log_directory() / 'client.log', 'r') as f:
            lines = f.readlines()
            assert lines[0].split('-')[-1].strip() == "Error starting client"
            assert lines[-2].split('-')[-1].strip() == "!! Exception: Incorrect number of parameters"

    # Wipe the log file
    (client_config_manager.get_log_directory() / 'client.log').unlink(missing_ok=True)

    t = Thread(target=run_thread, args=([None, 'notreal'],))
    t.start()
    t.join()

    # Should be no exception as it's caught internally
    assert not exc

    with open(client_config_manager.get_log_directory() / 'client.log', 'r') as f:
        lines = f.readlines()
        assert lines[0].split('-')[-1].strip() == "Error starting client"
        assert lines[-2].split('-')[-1].strip() == "!! Exception: Session type notreal does not exist."

    t = Thread(target=run_thread, args=([None, 'local'],))
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

    # Second line should be the magic terminator
    assert lines[1] == '=EOF='

    # Terminate the client
    client_rpc = xmlrpc.client.ServerProxy(
        f'http://localhost:{port}/rpc',
        allow_none=True,
        use_builtin_types=True
    )

    client_rpc.terminate()

    t.join()
