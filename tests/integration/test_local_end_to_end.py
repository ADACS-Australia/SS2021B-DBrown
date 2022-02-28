from tempfile import TemporaryDirectory, NamedTemporaryFile
from time import sleep
from uuid import UUID

import matplotlib
import numpy
import pytest

from finorch.sessions import LocalSession
from finorch.transport.exceptions import TransportGetJobSolutionException
from finorch.utils.job_status import JobStatus


class TestEndToEnd:

    BACKEND = None

    @classmethod
    def setup(cls):
        # grab the current matplotlib backend
        cls.BACKEND = matplotlib.get_backend()

        # set to a non-interactive backend, otherwise we need to manually close the figures to continue
        matplotlib.use('Agg')

        # This sleep gives previous python processes time to clean up and terminate
        sleep(0.5)

    @classmethod
    def teardown(cls):
        # restore the backend
        matplotlib.use(cls.BACKEND)

    @pytest.mark.filterwarnings("ignore")
    def test_end_to_end_single(self):
        with TemporaryDirectory() as tmpdir:
            session = LocalSession(exec_path=tmpdir)

            script = """
                # Add a Laser named L0 with a power of 1 W.
                l L0 P=1

                # Space attaching L0 <-> m1 with length of 0 m (default).
                s s0 L0.p1 m1.p1

                # Input mirror of cavity.
                m m1 R=0.99 T=0.01

                # Intra-cavity space with length of 1 m.
                s CAV m1.p2 m2.p1 L=1

                # End mirror of cavity.
                m m2 R=0.991 T=0.009

                # Power detectors on reflection, circulation and transmission.
                pd refl m1.p1.o
                pd circ m2.p1.i
                pd trns m2.p2.o

                # Scan over the detuning DOF of m1 from -180 deg to +180 deg with 400 points.
                xaxis(m1.phi, lin, -180, 180, 400)
            """

            # Start the test job
            job_identifier = session.start_job(script)

            # Test for a valid UUID
            try:
                UUID(job_identifier, version=4)
            except ValueError:
                assert False

            # Try to get the job solution before the job has finished, should raise an exception
            with pytest.raises(TransportGetJobSolutionException):
                session.get_job_solution(job_identifier)

            # Wait for the job to complete (Max wait of 30 seconds)
            for i in range(30):
                if session.get_job_status(job_identifier) == JobStatus.COMPLETED:
                    break

                sleep(1)

            # Check that the job really did finish in time
            assert i != 29

            # Check that the jobs are returned as a list, in this case the list should contain a single job
            jobs = session.get_jobs()
            assert len(jobs) == 1
            # validating the job identifier
            assert jobs[0].get('identifier', None) == job_identifier

            # Retrieve the solution object
            solution = session.get_job_solution(job_identifier)

            assert solution

            # Check that the solution can be plotted
            plt = solution.plot(logy=True)

            with NamedTemporaryFile() as f:
                list(plt.values())[0].savefig(f.name)

            # Retrieve file list for the job
            file_list = session.get_job_file_list(job_identifier)

            # List should contain at least the solution file
            assert len(file_list) > 0

            # Check that we can get the job's file list
            f = session.get_job_file(job_identifier, 'data.pickle')
            assert f is not None

            # Terminate the session
            session.terminate()

    @pytest.mark.filterwarnings("ignore")
    def test_end_to_end_multi(self):
        with TemporaryDirectory() as tmpdir:
            session = LocalSession(exec_path=tmpdir)

            job_identifiers = []

            for mirror_val in numpy.arange(0.5, 0.9, 0.01):
                script = f"""
                    # Add a Laser named L0 with a power of 1 W.
                    l L0 P=1

                    # Space attaching L0 <-> m1 with length of 0 m (default).
                    s s0 L0.p1 m1.p1

                    # Input mirror of cavity.
                    m m1 R={mirror_val} T=0.01

                    # Intra-cavity space with length of 1 m.
                    s CAV m1.p2 m2.p1 L=1

                    # End mirror of cavity.
                    m m2 R=0.991 T=0.009

                    # Power detectors on reflection, circulation and transmission.
                    pd refl m1.p1.o
                    pd circ m2.p1.i
                    pd trns m2.p2.o

                    # Scan over the detuning DOF of m1 from -180 deg to +180 deg with 400 points.
                    xaxis(m1.phi, lin, -180, 180, 400)
                """

                # Start the test job
                identifier = session.start_job(script)

                # Test for a valid UUID
                try:
                    UUID(identifier, version=4)
                except ValueError:
                    assert False

                with pytest.raises(TransportGetJobSolutionException):
                    session.get_job_solution(identifier)

                job_identifiers.append(identifier)

            # Wait for the jobs to complete (Max wait of 30 seconds)
            for i in range(30):
                finished = True
                for identifier in job_identifiers:
                    if session.get_job_status(identifier) != JobStatus.COMPLETED:
                        finished = False

                if finished:
                    break

                sleep(1)

            # Check that the jobs really did all finish in time
            assert i != 29

            # Check the jobs
            jobs = session.get_jobs()
            # checking if the number of the jobs are retrieved correctly
            assert len(job_identifiers) == len(jobs)

            for job in jobs:
                assert job.get('identifier', None) in job_identifiers

            for identifier in job_identifiers:
                # Retrieve the solution object
                solution = session.get_job_solution(identifier)

                assert solution

                # Check that the solution can be plotted
                plt = solution.plot(logy=True)

                with NamedTemporaryFile() as f:
                    list(plt.values())[0].savefig(f.name)

                # Retrieve file list for the job
                file_list = session.get_job_file_list(identifier)

                # List should contain at least the solution file
                assert len(file_list) > 0

            # Terminate the session
            session.terminate()
