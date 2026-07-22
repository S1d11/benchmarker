import pytest
import calculator


def test_add_is_sum():
    assert calculator.add(2, 3) == 5
    assert calculator.add(-1, 1) == 0


def test_divide_raises_on_zero():
    with pytest.raises(ValueError):
        calculator.divide(10, 0)


def test_divide_basic():
    assert calculator.divide(10, 2) == 5.0
    assert calculator.divide(0, 5) == 0.0
