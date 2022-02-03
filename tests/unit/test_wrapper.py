import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from threading import Thread
from time import sleep

from finorch.wrapper.wrapper import run
from tests.unit.local.test_local_client import SCRIPT
from tests.util import cd


def test_run():
    exc, stdout, stderr, orig_stdout, orig_stderr = None, None, None, None, None

    def run_thread(argv, wd):
        nonlocal exc, stdout, stderr, orig_stdout, orig_stderr
        exc = None

        # Save argv and output fds
        orig_args = sys.argv
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr

        with NamedTemporaryFile(delete=False) as out, NamedTemporaryFile(delete=False) as err:
            stdout = out.name
            stderr = err.name

            sys.stdout = open(out.name, 'w')
            sys.stderr = open(err.name, 'w')

            try:
                sys.argv = argv
                with cd(wd):
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
        with TemporaryDirectory() as tmpdir:
            t = Thread(target=run_thread, args=(argv, tmpdir,))
            t.start()
            t.join()

            # Should be no exception as it's caught internally
            assert not exc

            with open(str(Path(tmpdir) / 'wrapper.log'), 'r') as f:
                lines = f.readlines()
                assert lines[0].split('-')[-1].strip() == "Error starting wrapper"
                assert lines[-2].split('-')[-1].strip() == "!! Exception: Incorrect number of parameters"

            # Make sure output is flushed
            sys.stdout.flush()
            sys.stderr.flush()

            # Read the stdout and stderr files
            out = open(stdout, 'r').read()

            # Clean up stdout/stderr
            os.unlink(stdout)
            os.unlink(stderr)

            # Check the stdout/stderr outputs
            out = out.splitlines()
            assert out[0] == 'error'
            assert out[-1] == '=EOF='

    with TemporaryDirectory() as tmpdir:
        t = Thread(target=run_thread, args=([None, 'notreal'], tmpdir,))
        t.start()
        t.join()

        # Should be no exception as it's caught internally
        assert not exc

        with open(str(Path(tmpdir) / 'wrapper.log'), 'r') as f:
            lines = f.readlines()
            assert lines[0].split('-')[-1].strip() == "Error starting wrapper"
            assert lines[-2].split('-')[-1].strip() == "!! Exception: Session type notreal does not exist."

        # Read the stdout and stderr files
        out = open(stdout, 'r').read()

        # Clean up stdout/stderr
        os.unlink(stdout)
        os.unlink(stderr)

        # Check the stdout/stderr outputs
        out = out.splitlines()
        assert out[0] == 'error'
        assert out[-1] == '=EOF='

    with TemporaryDirectory() as tmpdir:
        t = Thread(target=run_thread, args=([None, 'local'], tmpdir,))

        with open(str(Path(tmpdir) / 'script.k'), 'w') as f:
            f.write(SCRIPT)

        t.start()
        t.join()

        # Wait for the session to complete
        sleep(0.5)

        # Read the stdout and stderr files
        out = open(stdout, 'r').read()
        err = open(stderr, 'r').read()

        # Clean up stdout/stderr
        os.unlink(stdout)
        os.unlink(stderr)

        # Stderr should not be empty (no errors)
        assert err
        assert not out
