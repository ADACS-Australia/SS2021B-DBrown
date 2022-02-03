import pytest

from finorch.transport.exceptions import TransportTerminateException, TransportGetJobFileException, \
    TransportGetJobFileListException, TransportGetJobStatusException, TransportGetJobsException
from finorch.transport.local import LocalTransport


class FakeRpc:
    def __init__(self):
        self.terminate_called = False

    def terminate(self):
        self.terminate_called = True

    def get_job_file(self, job_identifier, file_path):
        return None, "get_job_file_error"

    def get_job_file_list(self, job_identifier):
        return None, "get_job_file_list_error"

    def get_job_status(self, job_identifier):
        return None, "get_job_status_error"

    def get_jobs(self,):
        return None, "get_jobs_error"

    def stop_job(self, job_identifier):
        return None, "stop_job_error"


def test_terminate():
    transport = LocalTransport('a', 'b')
    transport._client_rpc = FakeRpc()

    with pytest.raises(TransportTerminateException):
        transport.terminate()

    assert not transport._client_rpc.terminate_called
    transport._connected = True

    transport.terminate()
    assert transport._client_rpc.terminate_called


def test_disconnect():
    transport = LocalTransport('a', 'b')

    with pytest.raises(NotImplementedError):
        transport.disconnect()


def test_get_job_file():
    transport = LocalTransport('a', 'b')
    transport._client_rpc = FakeRpc()

    with pytest.raises(TransportGetJobFileException):
        transport.get_job_file(None, None)


def test_get_job_file_list():
    transport = LocalTransport('a', 'b')
    transport._client_rpc = FakeRpc()

    with pytest.raises(TransportGetJobFileListException):
        transport.get_job_file_list(None)


def test_get_job_status():
    transport = LocalTransport('a', 'b')
    transport._client_rpc = FakeRpc()

    with pytest.raises(TransportGetJobStatusException):
        transport.get_job_status(None)


def test_get_jobs():
    transport = LocalTransport('a', 'b')
    transport._client_rpc = FakeRpc()

    with pytest.raises(TransportGetJobsException):
        transport.get_jobs()


def test_stop_job():
    transport = LocalTransport('a', 'b')

    with pytest.raises(NotImplementedError):
        transport.stop_job(None)


def test_update_job_parameters():
    transport = LocalTransport('a', 'b')

    with pytest.raises(NotImplementedError):
        transport.update_job_parameters(None, None)
