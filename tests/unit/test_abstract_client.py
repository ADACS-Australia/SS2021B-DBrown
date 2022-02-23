import tempfile
from pathlib import Path

import pytest

from finorch.sessions.abstract_client import AbstractClient, DatabaseNotConfiguredException


class TestClient(AbstractClient):
    __test__ = False

    def start_job(self, a):
        super().start_job(a)

    def stop_job(self, a):
        super().start_job(a)

    def get_jobs(self):
        super().get_jobs()

    def get_job_status(self, a):
        super().get_job_status(a)

    def get_job_file(self, a, b):
        super().get_job_file(a, b)

    def get_job_file_list(self, a):
        super().get_job_file_list(a)


def test_constructor():
    client = TestClient('TestKlass')
    assert client._exec_path is None
    assert client._xml_rpc_server is None
    assert client._session_klass == 'TestKlass'
    assert client._db is None


def test_set_server():
    client = TestClient(None)
    assert client._xml_rpc_server is None

    client.set_server(True)
    assert client._xml_rpc_server is True


def test_set_exec_path():
    client = TestClient(None)

    # Try letting the client choose an execution path
    client.set_exec_path(None)

    assert client._db is not None
    assert client._exec_path is not None
    assert (Path(client._exec_path) / 'db.sqlite3').exists()

    client = TestClient(None)

    # Now we'll set the exec path
    test_path = Path(tempfile.gettempdir()) / 'finorch_test'
    client.set_exec_path(str(test_path))

    assert test_path.is_dir()
    assert client._db is not None
    assert str(client._exec_path) == str(test_path)
    assert (Path(tempfile.gettempdir()) / 'finorch_test' / 'db.sqlite3').exists()


def test_db():
    client = TestClient(None)

    with pytest.raises(DatabaseNotConfiguredException):
        client.db()

    client._db = True

    assert client.db is True


def test_terminate():
    terminate_called = False

    class FakeServer():
        def terminate(self):
            nonlocal terminate_called
            terminate_called = True

    client = TestClient(None)

    # Terminate should not be called since the xml client isn't set
    client.terminate()
    assert terminate_called is False

    # Terminate should be called now
    client.set_server(FakeServer())
    client.terminate()
    assert terminate_called is True


def test_stubs():
    client = TestClient(None)

    with pytest.raises(NotImplementedError):
        client.start_job(None)

    with pytest.raises(NotImplementedError):
        client.get_jobs()

    with pytest.raises(NotImplementedError):
        client.get_job_status(None)

    with pytest.raises(NotImplementedError):
        client.get_job_file(None, None)

    with pytest.raises(NotImplementedError):
        client.get_job_file_list(None)
