from finorch.sessions.local.client import LocalClient
from finorch.sessions.abstract_session import AbstractSession
from finorch.sessions.local.wrapper import LocalWrapper
from finorch.transport.local import LocalTransport


class LocalSession(AbstractSession):
    callsign = "local"
    client_klass = LocalClient
    wrapper_klass = LocalWrapper
    transport_klass = LocalTransport

    def __init__(self, exec_path=None):
        """
        Creates a new local session that can be used to run finesse jobs in parallel locally.

        :param exec_path: The path to where jobs should be executed (and results stored), if not specified the path
        will be a temporary directory that is cleaned up when the client is terminated.
        """
        super().__init__()

        self._transport = LocalSession.transport_klass(self, exec_path)
        self._transport.connect()

    @property
    def transport(self):
        return self._transport
