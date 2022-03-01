from tempfile import TemporaryDirectory
from unittest import mock

from finorch.config.config import _ClientConfigManager, WrapperConfigManager
from finorch.utils.cd import cd


def test_client_get_port():
    with TemporaryDirectory() as tmp:
        with mock.patch('appdirs.user_config_dir', lambda *args: tmp):
            mgr = _ClientConfigManager()

            assert mgr.get_port() is None

            mgr.set_port(1234)
            assert int(mgr.get_port()) == 1234


def test_wrapper_get_port():
    with TemporaryDirectory() as tmp:
        with cd(tmp):
            mgr = WrapperConfigManager()

            assert mgr.get_port() is None

            mgr.set_port(1234)
            assert int(mgr.get_port()) == 1234
