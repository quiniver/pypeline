"""Simple test to verify pytest is working."""


def test_pytest_is_working():
    """This test should always pass if pytest is installed correctly."""
    assert True


def test_simple_assertion():
    """Another simple test."""
    x = 5
    y = 10
    assert x + y == 15
