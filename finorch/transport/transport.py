import abc

from finorch.transport.exceptions import TransportConnectionException


class Transport(abc.ABC):
    """
    This is the transport class that should be inherited from to build various transport types
    """

    def __init__(self, **kwargs):
        """
        Any transport setup should be done in this function

        :param kwargs: Any additional parameters that are required to initialise the transport
        :return: None
        """
        self.connected = False
        self.port = None

    def connect(self):
        """
        Connects the transport

        Should raise a TransportConnectionException in the event of a problem

        :return: None
        """

        if self.connected:
            raise TransportConnectionException("Transport is already connected")

    def disconnect(self):
        """
        Disconnects the transport

        :return: None
        """

        if not self.connected:
            raise TransportConnectionException("Transport is not connected")

    def start_job(self, katscript):
        """
        Starts a job using this transport using the model defined by the provided katscript

        Should raise a TransportStartJobException in the event of a problem

        :param katscript: The katscript defining the model to run
        :return: UUID representing the remote identifier for the job
        """

    def stop_job(self, job_identifier):
        """
        Stops a job using this transport with the provided job identifier

        Should raise a TransportStopJobException in the event of a problem

        :param job_identifier: The UUID of the job to stop
        :return: None
        """

    def get_jobs(self):
        """
        Fetches all remote jobs using this transport

        Should raise a TransportGetJobsException in the event of a problem

        :return: A list of dicts representing the details of the remote jobs
        """

    def get_job_solution(self, job_identifier):
        """
        Fetches the current (or final) Solution object for the specified job identifier

        Should raise a TransportGetJobSolutionException in the event of a problem

        :param job_identifier: the UUID of the job to get the solution for
        :return: A Finesse Solution object
        """

    def update_job_parameters(self, job_identifier, params):
        """
        Updates the parameters for the job specified by the specified job identifier

        Should raise a TransportUpdateJobParametersException in the event of a problem

        :param job_identifier: The UUID of the job to update the parameters of
        :param params: The new parameters
        :return: None
        """

    def get_job_file_list(self, job_identifier):
        """
        Retrieves the file list for the specified job identifier

        Should raise a TransportGetJobFileListException in the event of a problem

        :param job_identifier: the UUID of the job to fetch the file list for
        :return: A list of JobFile objects
        """

    def get_job_file(self, job_identifier, file_path):
        """
        Retrieves the specified file for the specified job identifier

        Should raise a TransportGetJobFileException in the event of a problem

        :param job_identifier: The UUID of the job to fetch the specified file for
        :param file_path: The path to the file to download
        :return: A bytes object representing the file that was downloaded
        """

    def terminate(self):
        """
        Stops the client and kills any finesse jobs that are running associated with the transport

        Should raise a TransportTerminateException in the event of a problem

        :return: None
        """
