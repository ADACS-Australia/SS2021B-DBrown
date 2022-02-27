import logging

from finorch.config.config import api_config_manager
from finorch.sessions.cit.client import CITClient
from finorch.sessions.abstract_session import AbstractSession
from finorch.sessions.cit.wrapper import CITWrapper
from finorch.transport.ssh import SshTransport


class CITSession(AbstractSession):
    callsign = "cit"
    client_klass = CITClient
    wrapper_klass = CITWrapper
    transport_klass = SshTransport

    def __init__(self, exec_path, username, python_path, env_file=None, *args, **kwargs):
        """
        Creates a new cit session that can be used to run finesse jobs in parallel on cit.

        :param exec_path: The path to where jobs should be executed (and results stored), if not specified the path
        will be a temporary directory that is cleaned up when the client is terminated.
        """
        super().__init__()

        self._transport = CITSession.transport_klass(
            self,
            exec_path,
            username=username,
            python_path=python_path,
            env_file=env_file,
            host="ldas-grid.ligo.caltech.edu",
            callsign=self.callsign,
            *args,
            **kwargs
        )

        cit_config = api_config_manager.get_section('cit')

        remote_port = cit_config.get('remote_port', None) if cit_config else None

        if remote_port:
            logging.info("Attempting to reconnect remote client last seen on remote port " + str(remote_port))
        else:
            logging.info("Attempting to connect remote client")

        remote_port = self._transport.connect(
            remote_port=remote_port
        )

        logging.info("Remote client connected on port " + str(remote_port))

        api_config_manager.set('cit', 'remote_port', str(remote_port))

    @property
    def transport(self):
        return self._transport
