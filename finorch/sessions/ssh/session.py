import logging

from finorch.config.config import api_config_manager
from finorch.sessions.abstract_session import AbstractSession
from finorch.sessions.local.client import LocalClient
from finorch.sessions.local.wrapper import LocalWrapper
from finorch.transport.ssh import SshTransport


class SshSession(AbstractSession):
    callsign = "ssh"
    client_klass = LocalClient
    wrapper_klass = LocalWrapper
    transport_klass = SshTransport

    def __init__(self, exec_path, username, python_path, env_file=None, *args, **kwargs):
        """
        Creates a new ssh session that can be used to run finesse jobs in parallel on a remote host over ssh where the
        remote host has no batch scheduler. This session uses a remote "Local" client over ssh.

        :param exec_path: The path to where jobs should be executed (and results stored), if not specified the path
        will be a temporary directory that is cleaned up when the client is terminated.
        """
        super().__init__()

        self._transport = SshSession.transport_klass(
            self,
            exec_path,
            username=username,
            python_path=python_path,
            env_file=env_file,
            callsign=self.callsign,
            *args,
            **kwargs
        )

        ssh_config = api_config_manager.get_section('ssh')

        remote_port = ssh_config.get(f'{kwargs["host"]}_remote_port', None) if ssh_config else None

        if remote_port:
            logging.info("Attempting to reconnect remote client last seen on remote port " + str(remote_port))
        else:
            logging.info("Attempting to connect remote client")

        remote_port = self._transport.connect(
            remote_port=remote_port
        )

        logging.info("Remote client connected on port " + str(remote_port))

        api_config_manager.set('ssh', f'{kwargs["host"]}_remote_port', str(remote_port))

    @property
    def transport(self):
        return self._transport
