import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

from finorch.utils.job_status import JobStatus

from finorch.sessions.database import Database


def test_add_job():
    with TemporaryDirectory() as tmpdir:
        db = Database(Path(tmpdir))
        identifier = str(uuid.uuid4())
        assert db.add_job(identifier) is True

        assert db.get_job_status(identifier) is JobStatus.PENDING


def test_update_job_status():
    with TemporaryDirectory() as tmpdir:
        db = Database(Path(tmpdir))
        identifier = str(uuid.uuid4())
        db.add_job(identifier)

        test_uuid = str(uuid.uuid4())
        assert db.update_job_status(test_uuid, JobStatus.RUNNING) == \
               (None, f"Job with with identifier {test_uuid} not found")

        assert db.update_job_status(identifier, JobStatus.RUNNING) is True

        assert db.get_job_status(identifier) is JobStatus.RUNNING
        test_uuid = str(uuid.uuid4())
        assert db.get_job_status(test_uuid) == (None, f"Job with with identifier {test_uuid} not found")


def test_get_jobs():
    with TemporaryDirectory() as tmpdir:
        db = Database(Path(tmpdir))
        identifier = str(uuid.uuid4())
        db.add_job(identifier)

        db.update_job_status(identifier, JobStatus.RUNNING)

        jobs = db.get_jobs()
        assert jobs[0]['identifier'] == identifier
        assert jobs[0]['status'] is JobStatus.RUNNING
        assert 'id' in jobs[0]
        assert 'start_time' in jobs[0]


def test_get_job_batch_id():
    with TemporaryDirectory() as tmpdir:
        db = Database(Path(tmpdir))
        identifier = str(uuid.uuid4())
        db.add_job(identifier)
        assert db.get_job_batch_id(identifier) is None

        identifier = str(uuid.uuid4())
        db.add_job(identifier, batch_id=1234)
        assert db.get_job_batch_id(identifier) == 1234

        test_uuid = str(uuid.uuid4())
        assert db.get_job_batch_id(test_uuid) == \
               (None, f"Job with with identifier {test_uuid} not found")
