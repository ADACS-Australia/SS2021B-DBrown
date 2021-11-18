import logging
import multiprocessing.pool
import os
import sys
import uuid
from tempfile import NamedTemporaryFile

from finorch.sessions.abstract_client import AbstractClient
from finorch.sessions.abstract_wrapper import AbstractWrapper


def _start_wrapper(_exec_path, _job_identifier, _session_klass, katscript):
    """
    Executed in another process to start the job
    :return: None
    """
    exec_dir = _exec_path / _job_identifier
    os.makedirs(exec_dir)
    os.chdir(exec_dir)

    n = NamedTemporaryFile()
    sys.stdout = open(n.name, "w")
    sys.stderr = sys.stdout

    with open(exec_dir / 'script.k', 'w') as f:
        f.write(katscript)

    AbstractWrapper.prepare_log_file()
    AbstractWrapper.start_wrapper(_session_klass)


class LocalClient(AbstractClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._pool = multiprocessing.pool.Pool()

    def start_job(self, katscript):
        job_identifier = str(uuid.uuid4())

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
