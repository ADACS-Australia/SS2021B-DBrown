import logging

from finorch.sessions.abstract_client import AbstractClient


class LocalClient(AbstractClient):
    def start_job(self, katscript):
        logging.info("Starting job with the following script")
        logging.info(katscript)

        return 1234

    def terminate(self):
        return super().terminate()
