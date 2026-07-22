import url


def test_repeated_keys_become_list():
    assert url.parse_query('a=1&a=2') == {'a': ['1', '2']}


def test_plus_decoded_to_space():
    assert url.parse_query('a=hello+world') == {'a': 'hello world'}


def test_percent_decoded():
    assert url.parse_query('a=hello%20world') == {'a': 'hello world'}
