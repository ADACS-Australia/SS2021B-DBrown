from finorch import __version__
from finorch.testfile import sum_test


def test_version():
    assert __version__ == '0.1.0'


def test_sum():
    assert sum_test(1, 2) == 3
