# SS2021B-DBrown (finorch)

This project is a finesse job orchestrator which facilitates running finesse jobs via an API and gathering information of
those jobs once it is completed. The project has been tested using python3 (3.8+).


## Project setup (development)

### Dependencies
Development Dependencies:-
* git
* poetry (`pip install poetry`)

### Steps
* Clone the project from the repo (`git clone ...`)
* Run `poetry install` to install the project dependencies to your environment.

***
## Usage

This project aims to allow running finesse jobs in different environments. For example, one should be able to run a 
finesse job locally or in a cluster remotely.

### Installing `finorch` remotely

In order to run finesse jobs in a remote environment (ex: OzSTAR), we need to install the `finorch` package there.

#### OzSTAR 
The following describes how to set up the remote environment for OzSTAR.

```shell
# Once you are logged in to OzSTAR

# install the dependencies
module load python/3.8.5
module load suitesparse/5.6.0-metis-5.1.0

# you can create a virtual environment to install finorch
virtualenv venv
. venv/bin/activate

# installing the finorch package
pip install finorch
```

We need to create an environment file to load up the dependencies in order to run jobs using the API.

In this case, a typical env file would like following:

```shell
#!/bin/bash

module load python/3.8.5
module load suitesparse/5.6.0-metis-5.1.0
```

### Installing `finorch` locally

To run a finesse job via the API (locally or remotely), we need to install the package locally. Again we can create
an environment and install `finorch` locally as follows:

```shell
# you can create a virtual environment to install finorch
virtualenv venv
. venv/bin/activate

# installing the finorch package
pip install finorch
```

### Creating Session

#### OzSTAR Session (for running jobs in OzSTAR)

Creating a Ozstar session requires the execution path location, user credentials to login to OzSTAR, the path to the python interpreter of the virtual environment and path to the environment file.

```python
from finorch.sessions import OzStarSession

session = OzStarSession(
    exec_path="<path/to/execute/jobs>",  # path to execute jobs ex: /home/<user>/finorch/jobs/
    username='<user>', # username to login to OzSTAR
    password='<*******>', # password to login to OzSTAR (Optional)
    python_path="<python/path>", # python path for the env in OzSTAR ex: /home/<user>/finorch/venv/bin/python
    env_file='<path/to/env/file>', # environment file to load necessary dependencies ex: /home/<user>/env.sh
)
```

#### Configure SSH keys

It is possible to configure SSH keys to log in to sessions that use the SSH Transport such as OzSTAR. This avoids having to use a password when creating the session. To configure the keys there are two helpers:-
```shell
# To configure a key for a session
# $ set_ssh_key <session name> <private key file>
set_ssh_key ozstar ~/keys/my_ozstar_key.key

# To remove a key from a session
# $ remove_ssh_key <session name>
remove_ssh_key ozstar
```

#### Local Session (for running jobs locally)

Creating a local session requires an execution path location, which is the directory where finesse jobs will be executed.
```python
from finorch.sessions import LocalSession

session = LocalSession(exec_path="/home/<user>/finorch/")
```


### Running a job using a session

Once a session is created (using any method described above), we can use the session to run finesse jobs. We need to 
provide the script (`KatScript`) for the job. For example:

```python
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
```

Using the `session` we have created earlier, now we can start job with the `script` as follows:

```python
job_id = session.start_job(script)
```

To get the status of a job we can do:

```python
status = session.get_job_status(job_identifier=job_id)
```

A job status of `500` means the job is completed. Once a job is completed, we can retrieve the job solution files:

```python
solution = session.get_job_solution(job_id)
```
The following table lists the all the available status and their corresponding numbers. 

STATUS | # 
--- | --- 
PENDING | 10
QUEUED | 40
RUNNING | 50
CANCELLED | 70
COMPLETED | 500

To get a list of job files, we can do:

```python
job_file_list = session.get_job_file_list(job_id)
```

This will return a list of lists where each of the list contains the filename, filepath, and filesize.

To get a single file for a job:

```python
f = session.get_job_file(job_id, '<filename>')
```

To get a list of all jobs for a transport we can call:

```python
jobs = session.get_jobs()
```

To terminate a session we need to call:

```python
session.terminate()
```

## License

The project is licensed under the MIT License. For more information, please refer to the [LICENSE](LICENSE) included in 
the root of the project.

## Acknowledgement

This project has been developed as part of the [ADACS](https://adacs.org.au/) program.