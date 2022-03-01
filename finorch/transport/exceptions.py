class TransportConnectionException(Exception):
    """
    Raised when a problem arises while connecting a transport
    """


class TransportStartJobException(Exception):
    """
    Raised when a problem arises while starting a job using a transport
    """


class TransportGetJobStatusException(Exception):
    """
    Raised when a problem arise while retrieving the status of a job
    """


class TransportGetJobSolutionException(Exception):
    """
    Raised when a problem arise while retrieving the solution for a job
    """


class TransportStopJobException(Exception):
    """
    Raised when a problem arises while stopping a job using a transport
    """


class TransportUpdateJobParametersException(Exception):
    """
    Raised when a problem arises while updating parameters of a remote job using a transport
    """


class TransportGetJobFileListException(Exception):
    """
    Raised when a problem arises while getting a job list of a remote job using a transport
    """


class TransportGetJobFileException(Exception):
    """
    Raised when a problem arises while downloading a job file of a remote job using a transport
    """


class TransportTerminateException(Exception):
    """
    Raised when a problem arise while terminating a client using a transport
    """
