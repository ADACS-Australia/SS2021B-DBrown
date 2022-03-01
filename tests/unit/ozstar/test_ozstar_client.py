import os
import sys
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory, NamedTemporaryFile
from unittest import TestCase
from unittest.mock import MagicMock

from finorch.sessions import OzStarSession
from finorch.sessions.ozstar.client import OzStarClient
from finorch.transport.exceptions import TransportStartJobException
from finorch.utils.job_status import JobStatus
from testfixtures import Replacer
from testfixtures.popen import MockPopen
from tests.unit.local.test_local_client import SCRIPT


class TestOzstarClient(TestCase):
    def setUp(self):
        self.popen = MockPopen()
        self.r = Replacer()
        self.r.replace('subprocess.Popen', self.popen)
        self.addCleanup(self.r.restore)

    def test_write_environment(self):
        client = OzStarClient(session_klass=OzStarSession)

        orig_environ = os.environ
        try:
            with NamedTemporaryFile() as temp_file:
                # Check that writing an empty environment file works as expected
                os.environ = {}
                client._write_environment(temp_file.name)
                self.assertEqual('', open(temp_file.name, 'r').read())

                # Check that writing an empty environment file works as expected
                os.environ = {}
                client._write_environment(temp_file.name)
                self.assertEqual('', open(temp_file.name, 'r').read())

                # Check that writing a simple environment variable works correctly
                os.environ['A'] = 'B'
                client._write_environment(temp_file.name)
                self.assertEqual('A="B"\n', open(temp_file.name, 'r').read())

                # Check that writing an variable with spaces works correctly
                os.environ['C'] = 'D E'
                client._write_environment(temp_file.name)
                self.assertEqual('A="B"\nC="D E"\n', open(temp_file.name, 'r').read())

                # Check that functions and aliases are correctly ignored
                os.environ['F()'] = 'G H'
                client._write_environment(temp_file.name)
                self.assertEqual('A="B"\nC="D E"\n', open(temp_file.name, 'r').read())
        finally:
            os.environ = orig_environ

    def test_submit_slurm_job_success(self):
        with TemporaryDirectory() as temp_dir:
            client = OzStarClient(session_klass=OzStarSession)
            client.set_exec_path(temp_dir)

            identifier = str(uuid.uuid4())

            working_dir = client._exec_path / identifier

            # Configure the popen data generation mock
            popen_command = f'sbatch {str(working_dir / "submit.sh")}'
            self.popen.set_command(
                popen_command,
                stdout='\n1234'.encode('utf-8'),
                stderr=b'stderr test',
            )

            self.assertEqual(client._submit_slurm_job(identifier, SCRIPT), 1234)
            self.assertTrue(Path(working_dir / 'submit.sh').is_file())
            self.assertTrue(Path(working_dir / 'script.k').is_file())

            self.assertEqual(open(Path(working_dir / 'script.k')).read(), SCRIPT)
            self.assertEqual(
                open(Path(working_dir / 'submit.sh'), 'r').read(),
                f"""#!/bin/bash
#SBATCH --time=01:00:00
#SBATCH --mem=16G
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1

. .env
{sys.executable} -m finorch.wrapper.wrapper ozstar
"""
            )

    def test_submit_slurm_sbatch_error(self):
        with TemporaryDirectory() as temp_dir:
            client = OzStarClient(session_klass=OzStarSession)
            client.set_exec_path(temp_dir)

            identifier = str(uuid.uuid4())

            working_dir = client._exec_path / identifier

            # Configure the popen data generation mock
            popen_command = f'sbatch {str(working_dir / "submit.sh")}'
            self.popen.set_command(
                popen_command,
                stdout='\n1234'.encode('utf-8'),
                stderr=b'stderr test',
                returncode=1
            )

            with self.assertRaises(TransportStartJobException):
                client._submit_slurm_job(identifier, SCRIPT)

    def test_submit_slurm_sbatch_result_error(self):
        with TemporaryDirectory() as temp_dir:
            client = OzStarClient(session_klass=OzStarSession)
            client.set_exec_path(temp_dir)

            identifier = str(uuid.uuid4())

            working_dir = client._exec_path / identifier

            # Configure the popen data generation mock
            popen_command = f'sbatch {str(working_dir / "submit.sh")}'
            self.popen.set_command(
                popen_command,
                stdout='\nnot real'.encode('utf-8'),
                stderr=b'stderr test',
            )

            with self.assertRaises(TransportStartJobException):
                client._submit_slurm_job(identifier, SCRIPT)

    def test_cancel_slurm_job(self):
        client = OzStarClient(session_klass=OzStarSession)

        job_id = 12345

        # Configure the popen data generation mock
        popen_command = f'scancel {job_id}'
        self.popen.set_command(
            popen_command
        )

        client._cancel_slurm_job(job_id)

    def test_start_job(self):
        with TemporaryDirectory() as temp_dir:
            client = OzStarClient(session_klass=OzStarSession)
            client.set_exec_path(temp_dir)
            client._submit_slurm_job = MagicMock()

            client._submit_slurm_job.return_value = 1234
            identifier = client.start_job(SCRIPT)

            self.assertEqual(client._submit_slurm_job.call_count, 1)
            self.assertEqual(client.get_job_status(identifier), JobStatus.QUEUED)

    def test_terminate(self):
        client = OzStarClient(session_klass=OzStarSession)
        client._xml_rpc_server = MagicMock()

        client.terminate()

        assert (client._xml_rpc_server.terminate.call_count == 1)

    def test_get_jobs(self):
        client = OzStarClient(session_klass=OzStarSession)
        client._submit_slurm_job = MagicMock()

        with TemporaryDirectory() as tmpdir:
            client.set_exec_path(tmpdir)

            client._submit_slurm_job.return_value = 1234
            identifier1 = client.start_job(SCRIPT)

            client._submit_slurm_job.return_value = 4321
            identifier2 = client.start_job(SCRIPT)

            jobs = client.get_jobs()
            assert jobs[0]['id'] == 1
            assert jobs[0]['identifier'] == identifier1
            assert jobs[0]['status'] == JobStatus.PENDING
            assert 'start_time' in jobs[0]

            assert jobs[1]['id'] == 2
            assert jobs[1]['identifier'] == identifier2
            assert jobs[1]['status'] == JobStatus.PENDING
            assert 'start_time' in jobs[1]

    def test_get_job_file(self):
        client = OzStarClient(session_klass=OzStarSession)
        client._submit_slurm_job = MagicMock()

        with TemporaryDirectory() as tmpdir:
            client.set_exec_path(tmpdir)

            client._submit_slurm_job.return_value = 1234
            identifier = client.start_job(SCRIPT)

            os.makedirs(client._exec_path / identifier, exist_ok=True)
            open(client._exec_path / identifier / 'script.k', 'w').close()
            open(client._exec_path / identifier / 'submit.sh', 'w').close()

            assert client.get_job_file(identifier, 'notreal') == \
                   (None, f"Unable to retrieve file {Path(tmpdir) / identifier / 'notreal'} "
                          "as the file does not exist.")

            assert client.get_job_file(identifier, 'script.k').decode('utf-8') == ''

    def test_get_job_file_list(self):
        client = OzStarClient(session_klass=OzStarSession)
        client._submit_slurm_job = MagicMock()

        with TemporaryDirectory() as tmpdir:
            client.set_exec_path(tmpdir)

            client._submit_slurm_job.return_value = 1234
            identifier = client.start_job(SCRIPT)

            os.makedirs(client._exec_path / identifier, exist_ok=True)
            open(client._exec_path / identifier / 'script.k', 'w').close()
            open(client._exec_path / identifier / 'submit.sh', 'w').close()

            tmp_identifier = str(uuid.uuid4())
            assert client.get_job_file_list(tmp_identifier) == \
                   (None, f"Unable to retrieve file list for the job identifier {tmp_identifier}")

            file_list = client.get_job_file_list(identifier)

            for file in ['script.k', 'submit.sh']:
                found = False
                for f in file_list:
                    if f[0] == file:
                        found = True
                        break

                if not found:
                    assert False

    def test_get_job_status(self):
        with TemporaryDirectory() as temp_dir:
            client = OzStarClient(session_klass=OzStarSession)
            client.set_exec_path(temp_dir)
            client._submit_slurm_job = MagicMock()

            client._submit_slurm_job.return_value = 1234
            identifier = client.start_job(SCRIPT)

            self.assertEqual(client._submit_slurm_job.call_count, 1)
            self.assertEqual(client.get_job_status(identifier), JobStatus.QUEUED)

            os.makedirs(client._exec_path / identifier, exist_ok=True)
            open(client._exec_path / identifier / 'started', 'w').close()
            self.assertEqual(client.get_job_status(identifier), JobStatus.RUNNING)

            open(client._exec_path / identifier / 'finished', 'w').close()
            self.assertEqual(client.get_job_status(identifier), JobStatus.COMPLETED)

    def test_stop_job(self):
        with TemporaryDirectory() as temp_dir:
            client = OzStarClient(session_klass=OzStarSession)
            client.set_exec_path(temp_dir)
            client._submit_slurm_job = MagicMock()
            client._cancel_slurm_job = MagicMock()

            client._submit_slurm_job.return_value = 1234
            identifier = client.start_job(SCRIPT)

            client.stop_job(identifier)
            self.assertEqual(client._cancel_slurm_job.call_count, 1)

            client._submit_slurm_job.return_value = 4321
            identifier = client.start_job(SCRIPT)

            os.makedirs(client._exec_path / identifier, exist_ok=True)
            open(client._exec_path / identifier / 'started', 'w').close()

            client._cancel_slurm_job = MagicMock()
            client.stop_job(identifier)
            self.assertEqual(client._cancel_slurm_job.call_count, 1)

            client._submit_slurm_job.return_value = 1342
            identifier = client.start_job(SCRIPT)

            os.makedirs(client._exec_path / identifier, exist_ok=True)
            open(client._exec_path / identifier / 'started', 'w').close()
            open(client._exec_path / identifier / 'finished', 'w').close()

            client._cancel_slurm_job = MagicMock()
            client.stop_job(identifier)
            self.assertEqual(client._cancel_slurm_job.call_count, 0)
