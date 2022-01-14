import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from finorch.utils.job_status import JobStatus

Base = declarative_base()


class Job(Base):
    __tablename__ = 'job'

    id = Column(Integer, primary_key=True)
    identifier = Column(String(40), unique=True)
    start_time = Column(DateTime, default=datetime.datetime.now, nullable=False)
    status = Column(Integer, default=JobStatus.PENDING)


class Database:
    def __init__(self, exec_path):
        """
        Initialises the database.

        :param exec_path: The path where the job output is kept. This is where the sqlite database will be stored.
        """
        # Set up the sqlite database
        self.engine = create_engine(f"sqlite:///{exec_path / 'db.sqlite3'}")

        Base.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def add_job(self, job_identifier):
        """
        Inserts a new job with the specified job identifier

        :param job_identifier: The job identifier
        :return: None
        """
        job = Job(
            identifier=job_identifier
        )

        self.session.add(job)
        self.session.commit()

    def get_job_status(self, job_identifier):
        """
        Gets the status of the specified job

        :param job_identifier: The identifier of the job
        :return: The status of the job (int) if the job was found, otherwise a Tuple of (None, *reason*)
        """
        results = self.session.query(Job).filter(Job.identifier == job_identifier)

        if results.count() != 1:
            return None, f"Job with with identifier {job_identifier} not found"

        return results.first().status

    def update_job_status(self, job_identifier, new_status):
        """
        Updates the status of a specified job

        :param job_identifier: The identifier of the job
        :param new_status: The new status for the job
        :return: None
        """
        results = self.session.query(Job).filter(Job.identifier == job_identifier)

        if results.count() != 1:
            return None, f"Job with with identifier {job_identifier} not found"

        results.first().status = new_status
        self.session.commit()

    def get_jobs(self):
        """
        Gets the list of jobs

        :return: A list of dictionaries containing job information
        """
        data = [r._asdict() for r in self.session.query(Job.id, Job.identifier, Job.start_time, Job.status).all()]

        return data
