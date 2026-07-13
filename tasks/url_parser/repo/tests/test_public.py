import url


def test_single_key():
    assert url.parse_query('a=1') == {'a': '1'}


def test_two_keys():
    assert url.parse_query('a=1&b=2') == {'a': '1', 'b': '2'}
