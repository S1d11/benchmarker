from hypothesis import given, strategies as st
import pytest
import calculator


@given(a=st.integers(), b=st.integers())
def test_add_commutative(a, b):
    assert calculator.add(a, b) == calculator.add(b, a)


@given(a=st.integers())
def test_add_identity(a):
    assert calculator.add(a, 0) == a
    assert calculator.add(0, a) == a


@given(a=st.integers(), b=st.integers(), c=st.integers())
def test_add_associative(a, b, c):
    assert calculator.add(calculator.add(a, b), c) == calculator.add(a, calculator.add(b, c))


@given(
    a=st.integers(min_value=-10000, max_value=10000),
    b=st.integers(min_value=-10000, max_value=10000).filter(lambda x: x != 0),
)
def test_divide_by_nonzero(a, b):
    assert calculator.divide(a, b) == a / b


@given(a=st.integers(min_value=-10000, max_value=10000))
def test_divide_by_zero_raises(a):
    with pytest.raises(ValueError):
        calculator.divide(a, 0)
