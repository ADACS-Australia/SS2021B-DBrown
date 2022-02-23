import logging
import os
import subprocess
import sys
import uuid
from pathlib import Path

from finorch.sessions.abstract_client import AbstractClient
from finorch.transport.exceptions import TransportStartJobException
from finorch.utils.cd import cd
from finorch.utils.job_status import JobStatus


SLURM_SCRIPT = """#!/bin/bash
#SBATCH --time=01:00:00
#SBATCH --mem=16G
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1

. .env
{python} -m finorch.wrapper.wrapper ozstar
"""


class OzStarClient(AbstractClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _write_environment(self, environment_file):
        with open(environment_file, "w") as f:
            for k, v in os.environ.items():
                if "()" in k:
                    continue
                else:
                    f.write(f'{k}="{v}"\n')

    def _submit_slurm_job(self, job_identifier, katscript):
        # Create the working directory for the job
        exec_dir = self._exec_path / job_identifier
        os.makedirs(exec_dir, exist_ok=True)

        with cd(exec_dir):
            # Write the katscript
            with open(exec_dir / 'script.k', 'w') as f:
                f.write(katscript)

            # Write the environment file
            self._write_environment(exec_dir / '.env')

            # Write the slurm submission script
            slurm_script_path = exec_dir / 'submit.sh'
            with open(slurm_script_path, 'w') as f:
                script = SLURM_SCRIPT.format(python=sys.executable)
                f.write(script)

            # Construct the sbatch command
            command = f"sbatch {slurm_script_path}"

            # Execute the sbatch command
            stdout = None
            try:
                stdout = subprocess.check_output(command, shell=True)
            except Exception:
                # Record the command and the output
                logging.error("Error: Command `{}` returned `{}`".format(command, stdout))
                raise TransportStartJobException("Unable to submit slurm job")

            # Record the command and the output
            logging.info("Success: Command `{}` returned `{}`".format(command, stdout))

            # Get the slurm id from the output
            try:
                return int(stdout.strip().split()[-1])
            except Exception:
                raise TransportStartJobException("Unable to submit slurm job")

    def _cancel_slurm_job(self, job_id):
        logging.info("Trying to terminate job {}...".format(job_id))

        # Construct the command
        command = "scancel {}".format(job_id)

        # Cancel the job
        stdout = subprocess.check_output(command, shell=True)

        # todo: Handle errors
        # Get the output
        logging.info("Command `{}` returned `{}`".format(command, stdout))

    def start_job(self, katscript):
        job_identifier = str(uuid.uuid4())

        logging.info("Starting job with the following script")
        logging.info(katscript)
        logging.info(job_identifier)

        slurm_id = self._submit_slurm_job(job_identifier, katscript)
        self.db.add_job(job_identifier, slurm_id)

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
            # Tell slurm to cancel the job
            self._cancel_slurm_job(self.db.get_job_batch_id(job_identifier))

            # Mark the job as cancelled
            self.db.update_job_status(job_identifier, JobStatus.CANCELLED)
