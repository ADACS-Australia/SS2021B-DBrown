import logging
import multiprocessing.pool
import os
import sys
import uuid

from finorch.sessions.abstract_client import AbstractClient
from finorch.sessions.abstract_wrapper import AbstractWrapper
from finorch.utils.job_status import JobStatus


def _start_wrapper(_exec_path, _job_identifier, _session_klass, katscript):
    """
    Executed in another process to start the job
    :return: None
    """
    exec_dir = _exec_path / _job_identifier
    os.makedirs(exec_dir)
    os.chdir(exec_dir)

    sys.stdout = open(str(exec_dir / 'out.log'), "w")
    sys.stderr = open(str(exec_dir / 'out.err'), "w")

    with open(exec_dir / 'script.k', 'w') as f:
        f.write(katscript)

    AbstractWrapper.prepare_log_file()
    AbstractWrapper.start_wrapper(_session_klass)


class LocalClient(AbstractClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Will create a pool with os.cpu_count() processes
        self._pool = multiprocessing.pool.Pool()

    def start_job(self, katscript):
        job_identifier = str(uuid.uuid4())

        self.db.add_job(job_identifier)

        logging.info("Starting job with the following script")
        logging.info(katscript)
        logging.info(job_identifier)

        self._pool.apply_async(
            _start_wrapper, (
                self._exec_path,
                job_identifier,
                self._session_klass,
                katscript
            )
        )

        return job_identifier

    def terminate(self):
        return super().terminate()

    def get_job_status(self, job_identifier):
        status = self.db.get_job_status(job_identifier)

        # If the job status is less than or equal to RUNNING, then we need to derive the current job status and update
        # the job status accordingly.
        new_status = status
        if status <= JobStatus.RUNNING:
            # Check if the job is completed, or started, or queued
            if os.path.exists(str(self._exec_path / job_identifier / 'finished')):
                new_status = JobStatus.COMPLETED
            elif os.path.exists(str(self._exec_path / job_identifier / 'started')):
                new_status = JobStatus.RUNNING
            else:
                new_status = JobStatus.QUEUED

        # Update the job if the status has changed
        if new_status != status:
            self.db.update_job_status(job_identifier, new_status)

        return new_status

    def get_job_solution(self, job_identifier):
        exec_dir = self._exec_path / job_identifier

        return open(exec_dir / 'data.pickle', 'rb').read()

    def get_job_file(self, job_identifier, file_path):
        full_file_path = str(self._exec_path / job_identifier / file_path)

        if os.path.exists(full_file_path):
            try:
                with open(full_file_path, 'rb') as f:
                    return f.read()
            except Exception:
                return None, f"Unable to retrieve file {full_file_path} as the file could not be read."

        return None, f"Unable to retrieve file {full_file_path} as the file does not exist."
