import pytest
import calculator


def test_add_basic():
    assert calculator.add(2, 3) == 5


def test_add_negative():
    assert calculator.add(-2, 3) == 1


def test_add_zero():
    assert calculator.add(0, 0) == 0


def test_divide_basic():
    assert calculator.divide(10, 2) == 5.0


def test_divide_zero_raises():
    with pytest.raises(ValueError):
        calculator.divide(10, 0)


def test_divide_zero_numerator():
    assert calculator.divide(0, 5) == 0.0
