import abc
import logging
import logging.handlers
import pathlib
import sys
import traceback
import xmlrpc.client
from threading import Thread
from time import sleep

from finorch.config.config import WrapperConfigManager
from finorch.utils.port import test_port_open
from finorch.utils.xmlrpc import XMLRPCServer


class AbstractWrapper(abc.ABC):
    """
    In this context a wrapper is the code that surrounds a finesse process. It is responsible for responding to
    communication from the client
    """
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

    def start(self):
        """
        Called by the wrapper to start the finesse thread

        :return: None
        """

        Thread(target=self._run).start()

    def _run(self):
        port = WrapperConfigManager().get_port()

        # Wait for the XMLRPC server to start
        while not test_port_open(port):
            sleep(0.1)  # pragma: no cover

        # Touch the 'started' file
        pathlib.Path('started').touch()

        try:
            logging.info("Starting finesse job")

            try:
                self.run()
            except Exception as exc:
                # An exception occurred, log the exception to the log file
                logging.error("Error running finesse job")
                logging.error(type(exc))
                logging.error(exc.args)
                logging.error(exc)

                # And log the stack trace
                exc_type, exc_value, exc_traceback = sys.exc_info()
                lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
                exc_log = ''.join('!! ' + line for line in lines)
                logging.error(exc_log)

            logging.info("Finesse job completed")
        finally:
            # Touch the 'finished' file
            pathlib.Path('finished').touch()

            try:
                # Kill the rpc server (If it's running). The deal with this is that when testing, since the
                # entire wrapper is itself running in a thread, the _run thread is not torn down with the
                # xml rpc server when terminate is called - therefor the xmlrpc server is killed, but this
                # thread is still running. When this code is hit, it will raise an exception
                wrapper_rpc_client = xmlrpc.client.ServerProxy(
                    f'http://localhost:{port}/rpc',
                    allow_none=True
                )
                wrapper_rpc_client.terminate()
            except Exception:
                pass

    def run(self):
        pass

    @staticmethod
    def prepare_log_file():
        """
        Creates the log file and sets up logging parameters
        :return: None
        """
        # Get the log file name
        log_file_name = pathlib.Path.cwd() / 'wrapper.log'

        from importlib import reload
        logging.shutdown()
        reload(logging)

        # Create the logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # Create the log handler
        handler = logging.handlers.RotatingFileHandler(log_file_name, maxBytes=10485760, backupCount=5)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))

        # Add the handler to the logger
        logger.addHandler(handler)

    @staticmethod
    def start_wrapper(session_klass):
        """
        Starts the wrapper.

        :return: None
        """
        wrapper = session_klass.wrapper_klass()

        # Create the XMLRPC server on a random port
        with XMLRPCServer(('localhost', 0)) as server:
            server.register_introspection_functions()

            wrapper.set_server(server)
            server.register_instance(wrapper)

            # Save the port in the wrapper configuration and start finesse
            port = server.server_address[1]
            logging.info(f"Port is {port}")
            WrapperConfigManager().set_port(port)

            wrapper.start()

            # Run the server's main loop
            server.serve_forever()
