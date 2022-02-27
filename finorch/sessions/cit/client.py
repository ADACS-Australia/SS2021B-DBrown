import logging
import os
import sys
import uuid
from pathlib import Path

from finorch.sessions.abstract_client import AbstractClient
from finorch.transport.exceptions import TransportStartJobException
from finorch.utils.cd import cd
from finorch.utils.job_status import JobStatus

SUBMIT_SCRIPT = """#!/bin/bash
. .env
{python} -m finorch.wrapper.wrapper cit
"""


class CitClient(AbstractClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _write_environment(self, environment_file):
        with open(environment_file, "w") as f:
            for k, v in os.environ.items():
                if "()" in k:
                    continue
                else:
                    f.write(f'{k}="{v}"\n')

    def _submit_condor_job(self, job_identifier, katscript):
        # Create the working directory for the job
        exec_dir = self._exec_path / job_identifier
        os.makedirs(exec_dir, exist_ok=True)

        with cd(exec_dir):
            # Write the katscript
            with open(exec_dir / 'script.k', 'w') as f:
                f.write(katscript)

            # Write the environment file
            self._write_environment(exec_dir / '.env')

            submit_script_path = exec_dir / 'submit.sh'
            with open(submit_script_path, 'w') as f:
                script = SUBMIT_SCRIPT.format(python=sys.executable)
                f.write(script)

            logging.info(f"Trying to submit from {exec_dir}")

            # Create the submit object from the dag and submit it
            # Retry up to 5 times before failing, condor submit is quite flakey at times
            for attempt in range(1, 6):
                try:
                    with cd(exec_dir):
                        import htcondor
                        submit = htcondor.Submit({
                            "universe": "scheduler",
                            "executable": "/bin/bash",
                            "arguments": "submit.sh",
                            "log": "log",
                            "output": "out",
                            "error": "error",
                            "request_cpus": "1",
                            "request_memory": "16G"
                        })

                        result = htcondor.Schedd().submit(submit, count=1)

                    # Record the command and the output
                    logging.info(f"Success: condor submit succeeded, got ClusterId={result.cluster()}")

                    # Return the condor ClusterId
                    return result.cluster()
                except Exception as e:
                    # Record the error occurred
                    logging.error(f"Error: condor submit failed, trying again {attempt}/5")
                    logging.error(e)

            raise TransportStartJobException("Unable to submit condor job. Condor submit failed 5 times in a row, "
                                             "assuming something is wrong.")

    def _cancel_condor_job(self, job_id):
        logging.info("Trying to terminate job {}...".format(job_id))

        import htcondor
        htcondor.Schedd().act(htcondor.JobAction.Hold, f"ClusterId == {job_id} && ProcID <= 1")

    def start_job(self, katscript):
        job_identifier = str(uuid.uuid4())

        logging.info("Starting job with the following script")
        logging.info(katscript)
        logging.info(job_identifier)

        condor_id = self._submit_condor_job(job_identifier, katscript)
        self.db.add_job(job_identifier, condor_id)

        return job_identifier

    def terminate(self):
        return super().terminate()

    def get_jobs(self):
        jobs = self.db.get_jobs()
        return jobs

    def get_job_status(self, job_identifier):
        status = self.db.get_job_status(job_identifier)

        # If the job status is less than or equal to RUNNING, then we need to derive the current job status and update
        # the job status accordingly.
        new_status = status
        if status <= JobStatus.RUNNING:
            # Check if the job is completed, or started, or queued
            p = Path(self._exec_path)
            if (p / job_identifier / 'finished').exists():
                new_status = JobStatus.COMPLETED
            elif (p / job_identifier / 'started').exists():
                new_status = JobStatus.RUNNING
            else:
                new_status = JobStatus.QUEUED

        # Update the job if the status has changed
        if new_status != status:
            self.db.update_job_status(job_identifier, new_status)

        return new_status

    def get_job_file(self, job_identifier, file_path):
        full_file_path = Path(self._exec_path / job_identifier / file_path)

        if full_file_path.exists():
            try:
                with open(full_file_path, 'rb') as f:
                    return f.read()
            except Exception:
                return None, f"Unable to retrieve file {full_file_path} as the file could not be read."

        return None, f"Unable to retrieve file {full_file_path} as the file does not exist."

    def get_job_file_list(self, job_identifier):
        full_path = Path(self._exec_path / job_identifier)
        if full_path.exists():
            # list the files
            file_list = list()

            for p in full_path.rglob('*.*'):
                file_list.append([p.name, str(p), p.stat().st_size])

            return file_list

        return None, f"Unable to retrieve file list for the job identifier {job_identifier}"

    def stop_job(self, job_identifier):
        # If the current job status is less than running, then cancel the job
        if self.get_job_status(job_identifier) < JobStatus.RUNNING:
            # Tell condor to cancel the job
            self._cancel_condor_job(self.db.get_job_batch_id(job_identifier))

            # Mark the job as cancelled
            self.db.update_job_status(job_identifier, JobStatus.CANCELLED)
