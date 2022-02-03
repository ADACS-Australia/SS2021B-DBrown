import os
import sys
import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from threading import Thread
from time import sleep

from finorch.utils.job_status import JobStatus

from finorch.sessions import LocalSession
from finorch.sessions.local.client import _start_wrapper, LocalClient


SCRIPT = """
    # Add a Laser named L0 with a power of 1 W.
    l L0 P=1

    # Space attaching L0 <-> m1 with length of 0 m (default).
    s s0 L0.p1 m1.p1

    # Input mirror of cavity.
    m m1 R=0.99 T=0.01

    # Intra-cavity space with length of 1 m.
    s CAV m1.p2 m2.p1 L=1

    # End mirror of cavity.
    m m2 R=0.991 T=0.009

    # Power detectors on reflection, circulation and transmission.
    pd refl m1.p1.o
    pd circ m2.p1.i
    pd trns m2.p2.o

    # Scan over the detuning DOF of m1 from -180 deg to +180 deg with 400 points.
    xaxis(m1.phi, lin, -180, 180, 400)
"""


def test_local_client_start_wrapper():
    exc, stdout, stderr, orig_stdout, orig_stderr = None, None, None, None, None

    def run_thread(exec_path, job_identifier, session_klass, katscript):
        nonlocal exc, stdout, stderr, orig_stdout, orig_stderr
        exc = None

        # Save output fds
        cwd = Path.cwd()
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr

        with NamedTemporaryFile() as out, NamedTemporaryFile() as err:
            stdout = out.name
            stderr = err.name

            sys.stdout = open(out.name, 'w')
            sys.stderr = open(err.name, 'w')

            try:
                _start_wrapper(exec_path, job_identifier, session_klass, katscript)
            except Exception as e:
                exc = e
            finally:
                # Make sure output is flushed
                sys.stdout.flush()
                sys.stderr.flush()

                # Restore argv and output fds
                os.chdir(cwd)
                sys.stdout = orig_stdout
                sys.stderr = orig_stderr

    with TemporaryDirectory() as tmpdir:
        identifier = str(uuid.uuid4())
        t = Thread(target=run_thread, args=(Path(tmpdir), identifier, LocalSession, SCRIPT))
        t.start()
        t.join()

        assert (Path(tmpdir) / identifier / 'script.k').exists()
        assert (Path(tmpdir) / identifier / 'out.log').exists()
        assert (Path(tmpdir) / identifier / 'out.err').exists()
        assert (Path(tmpdir) / identifier / 'data.pickle').exists()

        assert open(str((Path(tmpdir) / identifier / 'script.k')), 'r').read() == SCRIPT


def test_start_job():
    client = LocalClient(session_klass=LocalSession)
    with TemporaryDirectory() as tmpdir:
        client.set_exec_path(tmpdir)

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


def test_terminate():
    terminate_called = False

    class FakeServer():
        def terminate(self):
            nonlocal terminate_called
            terminate_called = True

    client = LocalClient(session_klass=LocalSession)

    # Terminate should not be called since the xml client isn't set
    client.terminate()
    assert terminate_called is False

    # Terminate should be called now
    client.set_server(FakeServer())
    client.terminate()
    assert terminate_called is True


def test_get_jobs():
    client = LocalClient(session_klass=LocalSession)
    with TemporaryDirectory() as tmpdir:
        client.set_exec_path(tmpdir)

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


def test_get_job_file():
    client = LocalClient(session_klass=LocalSession)
    with TemporaryDirectory() as tmpdir:
        client.set_exec_path(tmpdir)

        identifier = client.start_job(SCRIPT)

        while client.get_job_status(identifier) != JobStatus.COMPLETED:
            sleep(0.1)

        assert client.get_job_file(identifier, 'notreal') == \
               (None, f"Unable to retrieve file {Path(tmpdir) / identifier / 'notreal'} "
                      "as the file does not exist.")

        assert client.get_job_file(identifier, 'script.k').decode('utf-8') == SCRIPT


def test_get_job_file_list():
    client = LocalClient(session_klass=LocalSession)
    with TemporaryDirectory() as tmpdir:
        client.set_exec_path(tmpdir)

        identifier = client.start_job(SCRIPT)

        while client.get_job_status(identifier) != JobStatus.COMPLETED:
            sleep(0.1)

        tmp_identifier = str(uuid.uuid4())
        assert client.get_job_file_list(tmp_identifier) == \
               (None, f"Unable to retrieve file list for the job identifier {tmp_identifier}")

        file_list = client.get_job_file_list(identifier)

        for file in ['wrapper.ini', 'data.pickle', 'out.log', 'out.err']:
            found = False
            for f in file_list:
                if f[0] == file:
                    found = True
                    break

            if not found:
                assert False
