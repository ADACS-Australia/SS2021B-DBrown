import abc


class AbstractWrapper(abc.ABC):
    """
    In this context a wrapper is the code that surrounds a finesse process. It is responsible for responding to
    communication from the client
    """
