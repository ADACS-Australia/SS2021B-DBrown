from finorch.sessions.local.client import LocalClient
from finorch.sessions.abstract_session import AbstractSession
from finorch.sessions.local.wrapper import LocalWrapper


class LocalSession(AbstractSession):
    callsign = "local"

    def __init__(self):
        self.client = LocalClient()
        self.wrapper = LocalWrapper()
