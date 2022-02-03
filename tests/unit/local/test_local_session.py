from finorch.sessions import LocalSession


def test_transport():
    session = LocalSession()
    assert session.transport is session._transport

    session.terminate()
