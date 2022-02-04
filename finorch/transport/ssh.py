import logging
import select
import xmlrpc.client
from socketserver import BaseRequestHandler, ThreadingTCPServer
from threading import Thread
from time import sleep

import paramiko

from finorch.transport.abstract_transport import AbstractTransport
from finorch.transport.exceptions import TransportConnectionException, TransportTerminateException, \
    TransportGetJobFileException, TransportGetJobFileListException, TransportGetJobStatusException, \
    TransportGetJobsException


class SshTransport(AbstractTransport):
    def __init__(self, session, exec_path, *args, **kwargs):
        super().__init__(session, exec_path, *args, **kwargs)

        self._ssh_transport = None
        self._ssh_session = None

        self._host = kwargs['host']
        self._username = kwargs['username']
        self._ssh_password = kwargs['password']

        self._python_path = kwargs['python_path']
        self._env_file = kwargs.get('env_file', None)
        self._callsign = kwargs['callsign']
        self._ssh_port = kwargs.get('ssh_port', 22)

        self._remote_port = None

    def connect(self, *args, **kwargs):
        self._remote_port = kwargs['remote_port']
        self._remote_port = int(self._remote_port) if self._remote_port else None

        # Set up a connection to the remote server
        self._ssh_transport = paramiko.Transport((self._host, self._ssh_port))

        # Connect to the remote server
        self._ssh_transport.connect(
            hostkey=None,
            username=self._username,
            password=self._ssh_password,
            pkey=None
        )

        # First try to reconnect the previous port if it's set
        if self._remote_port:
            try:
                # Set up the ssh port forwarding
                self._forward_tunnel()

                # Connect the client rpc
                self._client_rpc = xmlrpc.client.ServerProxy(
                    f'http://localhost:{self._port}/rpc',
                    allow_none=True,
                    use_builtin_types=True
                )

                self._client_rpc.system.listMethods()

                # We're connected
                self._connected = True

                return self._remote_port
            except Exception:
                # Remote client is dead or invalid
                self._connection.server_close()
                self._connected = False

        # Remote client isn't running, start the remote client
        session = self._ssh_transport.open_channel("session")

        # Always try to make the execution directory and change to it
        command = f"bash --login -c \"mkdir -p {self.exec_path} && cd {self.exec_path} && "
        if self._env_file:
            command += f"source {self._env_file} && "

        command += f"{self._python_path} -m finorch.client.client {self._callsign}\""

        # Run the command to start the remote client
        logging.info(f"Executing command: {command}")
        session.exec_command(command)

        # Wait for the connection to close
        stdout, stderr = b'', b''
        while True:  # monitoring process
            # Reading from output streams
            while session.recv_ready():
                stdout += session.recv(1000)
            while session.recv_stderr_ready():
                stderr += session.recv_stderr(1000)
            if session.exit_status_ready():  # If completed
                break
            sleep(0.1)

        stdout = stdout.decode('utf-8')
        stderr = stderr.decode('utf-8')

        # Check that the command finished successfully
        if session.exit_status:
            raise TransportConnectionException(
                f"Unable to start remote server.\nstdout:\n{stdout}\n\nstderr:\n{stderr}\n"
            )

        # Finished with the session now
        session.close()

        # Parse the remote stdout
        stdout = stdout.splitlines()

        # Check if the client started successfully
        if stdout[0] == "error":
            # Report the error from the client
            raise TransportConnectionException('\n'.join(stdout[1:]))

        # Try to parse the first line of the output from the client as the port it is running on
        try:
            self._remote_port = int(stdout[0])
        except ValueError:
            raise TransportConnectionException(f"Unable to parse the port. Got {stdout[0]}")

        # Set up the ssh port forwarding
        self._forward_tunnel()

        # Connect the client rpc
        self._client_rpc = xmlrpc.client.ServerProxy(
            f'http://localhost:{self._port}/rpc',
            allow_none=True,
            use_builtin_types=True
        )

        self._client_rpc.set_exec_path(self.exec_path)

        # We're connected
        self._connected = True

        return self._remote_port

    def disconnect(self):
        raise NotImplementedError()

    def get_job_file(self, job_identifier, file_path):
        status = self._client_rpc.get_job_file(job_identifier, file_path)
        if type(status) is bytes:
            return status
        else:
            raise TransportGetJobFileException(status[1])

    def get_job_file_list(self, job_identifier):
        status = self._client_rpc.get_job_file_list(job_identifier)
        if type(status) is list:
            return status
        else:
            raise TransportGetJobFileListException(status[1])

    def get_job_status(self, job_identifier):
        status = self._client_rpc.get_job_status(job_identifier)
        if type(status) is int:
            return status
        else:
            raise TransportGetJobStatusException(status[1])

    def get_jobs(self):
        status = self._client_rpc.get_jobs()
        if type(status) is list:
            return status
        else:
            raise TransportGetJobsException(status[1])

    def start_job(self, katscript):
        return self._client_rpc.start_job(katscript)

    def stop_job(self, job_identifier):
        raise NotImplementedError()

    def update_job_parameters(self, job_identifier, params):
        raise NotImplementedError()

    def terminate(self):
        print(self._connected)
        if not self._connected:
            raise TransportTerminateException("Client is not connected")

        self._client_rpc.terminate()
        self._connected = False

    """
    SSH supporting code. Adapted from the following:-
    https://github.com/paramiko/paramiko/blob/main/demos/forward.py
    https://stackoverflow.com/questions/11294919/port-forwarding-with-paramiko
    """

    class SshForwardServer(ThreadingTCPServer):
        daemon_threads = True
        allow_reuse_address = True

    class SshHandler(BaseRequestHandler):
        chain_host = None
        chain_port = None
        ssh_transport = None

        def handle(self):
            try:
                chan = self.ssh_transport.open_channel(
                    "direct-tcpip",
                    (self.chain_host, self.chain_port),
                    self.request.getpeername(),
                )
            except Exception as e:
                logging.error(
                    "Incoming request to %s:%d failed: %s"
                    % (self.chain_host, self.chain_port, repr(e))
                )
                return
            if chan is None:
                logging.error(
                    "Incoming request to %s:%d was rejected by the SSH server."
                    % (self.chain_host, self.chain_port)
                )
                return

            logging.info(
                "Connected!  Tunnel open %r -> %r -> %r"
                % (
                    self.request.getpeername(),
                    chan.getpeername(),
                    (self.chain_host, self.chain_port),
                )
            )
            while True:
                r, w, x = select.select([self.request, chan], [], [])
                if self.request in r:
                    data = self.request.recv(1024)
                    if len(data) == 0:
                        break
                    chan.send(data)
                if chan in r:
                    data = chan.recv(1024)
                    if len(data) == 0:
                        break
                    self.request.send(data)

            peername = self.request.getpeername()
            chan.close()
            self.request.close()
            logging.info("Tunnel closed from %r" % (peername,))

    def _forward_tunnel(self):
        # this is a little convoluted, but lets me configure things for the Handler
        # object.  (SocketServer doesn't give Handlers any way to access the outer
        # server normally.)
        class SubHander(SshTransport.SshHandler):
            chain_host = "localhost"
            chain_port = self._remote_port
            ssh_transport = self._ssh_transport

        self._connection = SshTransport.SshForwardServer(("localhost", 0), SubHander)

        # Get the local port
        self._port = self._connection.server_address[1]

        # Start a thread to run the server
        def server_thread():
            self._connection.serve_forever()

        Thread(target=server_thread, daemon=True).start()
