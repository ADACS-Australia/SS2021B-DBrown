from tempfile import TemporaryDirectory, NamedTemporaryFile
from time import sleep
from uuid import UUID

from finorch.sessions import LocalSession
from finorch.utils.job_status import JobStatus
import numpy


def test_end_to_end_single():
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

        # Wait for the job to complete (Max wait of 30 seconds)
        for i in range(30):
            if session.get_job_status(job_identifier) == JobStatus.COMPLETED:
                break

            sleep(1)

        # Check that the jobs really did all finish in time
        assert i != 29

        # Retrieve the solution object
        solution = session.get_job_solution(job_identifier)

        assert solution

        # Check that the solution can be plotted
        plt = solution.plot(logy=True)

        with NamedTemporaryFile() as f:
            list(plt.values())[0].savefig(f.name)

        # Terminate the session
        session.terminate()


def test_end_to_end_multi():
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

        for identifier in job_identifiers:
            # Retrieve the solution object
            solution = session.get_job_solution(identifier)

            assert solution

            # Check that the solution can be plotted
            plt = solution.plot(logy=True)

            with NamedTemporaryFile() as f:
                list(plt.values())[0].savefig(f.name)

        # Terminate the session
        session.terminate()
