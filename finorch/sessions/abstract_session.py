import abc
from tempfile import NamedTemporaryFile

import finesse

from finorch.transport.exceptions import TransportGetJobSolutionException
from finorch.utils.job_status import JobStatus


class AbstractSession(abc.ABC):
    def __init__(self):
        self._transport = None

    def start_job(self, script):
        return self._transport.start_job(script)

    def get_job(self, job_identifier):
        return self._transport.get_job(job_identifier)

    def get_jobs(self):
        return self._transport.get_jobs()

    def get_job_status(self, job_identifier):
        return self._transport.get_job_status(job_identifier)

    def get_job_file(self, job_identifier, file_path):
        return self._transport.get_job_file(job_identifier, file_path)

    def get_job_file_list(self, job_identifier):
        return self._transport.get_job_file_list(job_identifier)

    def get_job_solution(self, job_identifier):
        if self.get_job_status(job_identifier) <= JobStatus.RUNNING:
            raise TransportGetJobSolutionException("Can't get solution as job is not yet finished")

        result = self._transport.get_job_file(job_identifier, 'data.pickle')

        with NamedTemporaryFile() as f:
            f.write(result)
            return finesse.load(f.name, 'pickle')

    def terminate(self):
        self._transport.terminate()
