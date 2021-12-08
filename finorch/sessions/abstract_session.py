import abc


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

    def get_job_solution(self, job_identifier):
        return self._transport.get_job_solution(job_identifier)

    def terminate(self):
        self._transport.terminate()
