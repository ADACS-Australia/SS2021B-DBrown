import logging

from finorch.config.config import api_config_manager
from finorch.sessions.ozstar.client import OzStarClient
from finorch.sessions.abstract_session import AbstractSession
from finorch.sessions.ozstar.wrapper import OzStarWrapper
from finorch.transport.ssh import SshTransport


class OzStarSession(AbstractSession):
    callsign = "ozstar"
    client_klass = OzStarClient
    wrapper_klass = OzStarWrapper
    transport_klass = SshTransport

    def __init__(self, exec_path, username, python_path, env_file=None, *args, **kwargs):
        """
        Creates a new ozstar session that can be used to run finesse jobs in parallel on ozstar.

        :param exec_path: The path to where jobs should be executed (and results stored), if not specified the path
        will be a temporary directory that is cleaned up when the client is terminated.
        """
        super().__init__()

        self._transport = OzStarSession.transport_klass(
            self,
            exec_path,
            username=username,
            python_path=python_path,
            env_file=env_file,
            host="farnarkle1.hpc.swin.edu.au",
            callsign=self.callsign,
            *args,
            **kwargs
        )

        ozstar_config = api_config_manager.get_section('ozstar')

        remote_port = ozstar_config.get('remote_port', None) if ozstar_config else None

        if remote_port:
            logging.info("Attempting to reconnect remote client last seen on remote port " + str(remote_port))
        else:
            logging.info("Attempting to connect remote client")

        remote_port = self._transport.connect(
            remote_port=remote_port
        )

        logging.info("Remote client connected on port " + str(remote_port))

        api_config_manager.set('ozstar', 'remote_port', str(remote_port))

    @property
    def transport(self):
        return self._transport
