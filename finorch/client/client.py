import logging
import logging.handlers
import sys
import traceback
from tempfile import NamedTemporaryFile
from xmlrpc.server import SimpleXMLRPCRequestHandler
from xmlrpc.server import SimpleXMLRPCServer

from finorch.config.config import client_config_manager
from finorch.sessions import session_map


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/rpc',)


class XMLRPCServer(SimpleXMLRPCServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._quit = False

    def serve_forever(self, **kwargs):
        """
        Overrides the serve_forever function to wait for the server to be ready to quit

        :param kwargs: N/A
        :return: None
        """
        while not self._quit:
            self.handle_request()

    def terminate(self):
        """
        Marks the server as ready for termination

        :return: None
        """

        self._quit = True


def start_client():
    """
    Starts the client.

    :return: None
    """
    # Get the session from the provided session parameter
    if len(sys.argv) != 2:
        raise Exception("Incorrect number of parameters")

    if sys.argv[1] not in session_map:
        raise Exception(f"Session type {sys.argv[1]} does not exist.")

    session = session_map[sys.argv[1]]()

    # Create the XMLRPC server on a random port
    with XMLRPCServer(('localhost', 0), requestHandler=RequestHandler) as server:
        server.register_introspection_functions()

        session.client.set_server(server)
        server.register_instance(session.client)

        # Save the port in the client configuration
        port = server.server_address[1]
        client_config_manager.set_port(port)

        # Return the port via stdout to the caller
        print(server.server_address[1], flush=True)
        print("=EOF=")

        logging.info(sys.stdout.fileno())
        logging.info(sys.stderr.fileno())

        n = NamedTemporaryFile()
        sys.stdout = open(n.name, "w")
        sys.stderr = sys.stdout

        # Run the server's main loop
        server.serve_forever()


def prepare_log_file():
    """
    Creates the log file and sets up logging parameters
    :return: None
    """
    # Get the log file name
    log_file_name = client_config_manager.get_log_directory() / 'client.log'

    # Create the logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create the log handler
    handler = logging.handlers.RotatingFileHandler(log_file_name, maxBytes=10485760, backupCount=5)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))

    # Add the handler to the logger
    logger.addHandler(handler)


if __name__ == '__main__':
    # Attempt to start the client and if there is an error print error to stdout, and the stack trace to stderr.
    try:
        prepare_log_file()
        start_client()
    except Exception as exc:
        # An exception occurred, log the exception to the log file
        logging.error("Error starting client")
        logging.error(type(exc))
        logging.error(exc.args)
        logging.error(exc)

        # And log the stack trace
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        exc_log = ''.join('!! ' + line for line in lines)
        logging.error(exc_log)

        # Log to stdout and stderr
        print("error", flush=True)
        print(exc_log, flush=True)
        print("=EOF=")
