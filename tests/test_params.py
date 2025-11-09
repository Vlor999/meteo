"""Test the params module."""

from src.params import FILE, LIMIT_EST, LIMIT_NORTH, LIMIT_SOUTH, LIMIT_WEST


def test_file_constant():
    """Test that FILE constant is properly defined."""
    assert FILE == "data/MN_01_2000-2009.csv"
    assert isinstance(FILE, str)


def test_limit_constants():
    """Test that all limit constants are properly defined."""
    assert LIMIT_WEST == "005 48 W"
    assert LIMIT_EST == "10 E"
    assert LIMIT_NORTH == "51 30 N"
    assert LIMIT_SOUTH == "41 N"

    # Verify they are all strings
    assert isinstance(LIMIT_WEST, str)
    assert isinstance(LIMIT_EST, str)
    assert isinstance(LIMIT_NORTH, str)
    assert isinstance(LIMIT_SOUTH, str)
