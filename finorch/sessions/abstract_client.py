import abc
import atexit
import os
from pathlib import Path
from tempfile import TemporaryDirectory


class AbstractClient(abc.ABC):
    def __init__(self, session_klass):
        self._exec_path = None
        self._xml_rpc_server = None
        self._session_klass = session_klass

    def set_server(self, server):
        """
        Sets the XMLRPC server where required. This is then used by the terminate() command

        :param server: The xmlrpc server instance
        :return: None
        """

        self._xml_rpc_server = server

    def set_exec_path(self, path):
        if path:
            # Path is already defined, so set up the path and make sure the directory is created
            self._exec_path = Path(path)
            os.makedirs(self._exec_path, exist_ok=True)
        else:
            # If the path is not specified, create a temporary directory and mark it for cleanup when the client exits
            tmpdir = TemporaryDirectory()
            self._exec_path = Path(tmpdir.name)
            atexit.register(lambda: tmpdir.cleanup())

    def terminate(self):
        """
        Called to terminate the XMLRPC server

        :return: True if the server was terminated successfully, False otherwise
        """

        if self._xml_rpc_server:
            self._xml_rpc_server.terminate()

        return True