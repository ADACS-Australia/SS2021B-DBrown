import pytest

from finorch.transport.abstract_transport import AbstractTransport
from finorch.transport.exceptions import TransportConnectionException


class TestTransport(AbstractTransport):
    __test__ = False

    def start_job(self, a):
        super().start_job(a)

    def get_jobs(self):
        super().get_jobs()

    def get_job_status(self, a):
        super().get_job_status(a)

    def get_job_file(self, a, b):
        super().get_job_file(a, b)

    def get_job_file_list(self, a):
        super().get_job_file_list(a)

    def terminate(self):
        super().terminate()

    def connect(self):
        super().connect()

    def disconnect(self):
        super().disconnect()

    def stop_job(self, a):
        super().stop_job(a)

    def update_job_parameters(self, job_identifier, params):
        super().update_job_parameters(job_identifier, params)


def test_constructor():
    transport = TestTransport('a', 'b')

    assert transport._session == 'a'
    assert transport._exec_path == 'b'
    assert transport._connected is False
    assert transport._port is None


def test_exec_path():
    transport = TestTransport('a', 'b')
    assert transport.exec_path == 'b'


def test_connect():
    transport = TestTransport('a', 'b')

    transport.connect()

    transport._connected = True
    with pytest.raises(TransportConnectionException):
        transport.connect()


def test_disconnect():
    transport = TestTransport('a', 'b')

    with pytest.raises(TransportConnectionException):
        transport.disconnect()

    transport._connected = True
    transport.disconnect()


def test_stubs():
    transport = TestTransport('a', 'b')

    with pytest.raises(NotImplementedError):
        transport.start_job(None)

    with pytest.raises(NotImplementedError):
        transport.get_jobs()

    with pytest.raises(NotImplementedError):
        transport.get_job_status(None)

    with pytest.raises(NotImplementedError):
        transport.get_job_file(None, None)

    with pytest.raises(NotImplementedError):
        transport.get_job_file_list(None)

    with pytest.raises(NotImplementedError):
        transport.stop_job(None)

    with pytest.raises(NotImplementedError):
        transport.update_job_parameters(None, None)

    with pytest.raises(NotImplementedError):
        transport.terminate()
