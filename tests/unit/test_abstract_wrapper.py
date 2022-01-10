import logging
import pathlib
import sys
import xmlrpc.client
from tempfile import TemporaryDirectory
from threading import Thread
from time import sleep

from finorch.config.config import WrapperConfigManager
from finorch.sessions.abstract_client import AbstractClient
from finorch.sessions.abstract_session import AbstractSession
from finorch.sessions.abstract_wrapper import AbstractWrapper
from tests.util import cd


def test_constructor():
    cls = AbstractWrapper()
    assert cls._xml_rpc_server is None


def test_set_server():
    cls = AbstractWrapper()
    cls.set_server("test server")
    assert cls._xml_rpc_server == "test server"


def test_prepare_log_file():
    with TemporaryDirectory() as tmpdir:
        with cd(tmpdir):
            AbstractWrapper.prepare_log_file()

            logging.info("Test Log Entry")

            with open(pathlib.Path.cwd() / 'wrapper.log', 'r') as f:
                assert f.readline().split('-')[-1].strip() == "Test Log Entry"


def test_start_wrapper():
    # Dummy abstract session
    class MyAbstractSession(AbstractSession):
        callsign = "local"
        client_klass = AbstractClient
        wrapper_klass = AbstractWrapper

    with TemporaryDirectory() as tmpdir:
        def exec_thread():
            with cd(tmpdir):
                AbstractWrapper.prepare_log_file()
                AbstractWrapper.start_wrapper(MyAbstractSession)

        t = Thread(target=exec_thread)
        t.start()

        sleep(0.5)

        # Check that a port config was set
        assert int(WrapperConfigManager(tmpdir).get_port())

        # Thread should finish almost instantly
        assert not t.is_alive()


def test_start_wrapper_exception():
    # Dummy Wrapper
    class MyWrapper(AbstractWrapper):
        def run(self):
            raise Exception("Exception")

    # Dummy abstract session
    class MyAbstractSession(AbstractSession):
        callsign = "local"
        client_klass = AbstractClient
        wrapper_klass = MyWrapper

    with TemporaryDirectory() as tmpdir:
        def exec_thread():
            with cd(tmpdir):
                AbstractWrapper.prepare_log_file()
                AbstractWrapper.start_wrapper(MyAbstractSession)

        t = Thread(target=exec_thread)
        t.start()

        sleep(0.5)

        # Check that a port config was set
        assert int(WrapperConfigManager(tmpdir).get_port())

        # Thread should finish almost instantly
        assert not t.is_alive()


def test_terminate():
    terminating = False
    terminated = False

    # Dummy Wrapper
    class MyWrapper(AbstractWrapper):
        def run(self):
            while not terminating:
                sleep(0.1)

            print("Terminating", file=sys.stderr)
            nonlocal terminated
            terminated = True

    # Dummy abstract session
    class MyAbstractSession(AbstractSession):
        callsign = "dummy"
        client_klass = AbstractClient
        wrapper_klass = MyWrapper

    with TemporaryDirectory() as tmpdir:
        def exec_thread():
            with cd(tmpdir):
                AbstractWrapper.prepare_log_file()
                AbstractWrapper.start_wrapper(MyAbstractSession)

                while not terminated:
                    sleep(0.1)

                sleep(0.1)

        t = Thread(target=exec_thread)
        t.start()

        sleep(0.5)

        port = int(WrapperConfigManager(tmpdir).get_port())

        client_rpc = xmlrpc.client.ServerProxy(
            f'http://localhost:{port}/rpc',
            allow_none=True,
            use_builtin_types=True
        )

        assert t.is_alive()

        client_rpc.terminate()

        terminating = True

        sleep(0.5)

        # Thread should be finished
        assert not t.is_alive()
