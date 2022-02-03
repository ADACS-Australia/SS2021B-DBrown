import logging
import sys
import traceback

from finorch.sessions import session_map
from finorch.sessions.abstract_wrapper import AbstractWrapper


def run():
    # Attempt to start the wrapper and if there is an error print error to stdout, and the stack trace to stderr.
    try:
        AbstractWrapper.prepare_log_file()

        if len(sys.argv) != 2:
            raise Exception("Incorrect number of parameters")

        if sys.argv[1] not in session_map:
            raise Exception(f"Session type {sys.argv[1]} does not exist.")

        # Get the wrapper from the provided session parameter
        session_klass = session_map[sys.argv[1]]

        AbstractWrapper.start_wrapper(session_klass)
    except Exception as exc:
        # An exception occurred, log the exception to the log file
        logging.error("Error starting wrapper")
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


if __name__ == '__main__':
    run()
