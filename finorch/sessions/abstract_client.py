import abc


class AbstractClient(abc.ABC):
    def __init__(self):
        self._xml_rpc_server = None

    def set_server(self, server):
        """
        Sets the XMLRPC server where required. This is then used by the terminate() command

        :param server: The xmlrpc server instance
        :return: None
        """

        self._xml_rpc_server = server

    def terminate(self):
        """
        Called to terminate the XMLRPC server

        :return: True if the server was terminated successfully, False otherwise
        """

        if self._xml_rpc_server:
            self._xml_rpc_server.terminate()

        return True
