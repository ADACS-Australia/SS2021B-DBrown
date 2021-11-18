import abc


class AbstractSession(abc.ABC):
    def __init__(self):
        self._transport = None

    def start_job(self, script):
        return self._transport.start_job(script)

    def terminate(self):
        self._transport.terminate()
