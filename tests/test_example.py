def test_example():
    """Example test to verify pytest works."""
    assert 1 + 1 == 2


def test_example_with_parametrize():
    """Example parametrized test."""
    numbers = [1, 2, 3, 4, 5]
    for num in numbers:
        assert num > 0
