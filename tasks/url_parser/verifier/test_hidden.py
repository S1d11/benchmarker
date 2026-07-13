import url


def test_repeated_key_collects_list():
    assert url.parse_query('a=1&a=2') == {'a': ['1', '2']}


def test_repeated_key_many():
    assert url.parse_query('a=1&a=2&a=3') == {'a': ['1', '2', '3']}


def test_plus_decoded_to_space():
    assert url.parse_query('a=hello+world') == {'a': 'hello world'}


def test_percent_decoded():
    assert url.parse_query('a=hello%20world') == {'a': 'hello world'}


def test_repeated_with_plus_and_percent():
    assert url.parse_query('a=hello+world&a=foo%20bar') == {'a': ['hello world', 'foo bar']}


def test_empty_query():
    assert url.parse_query('') == {}


def test_none_query():
    assert url.parse_query(None) == {}


def test_skip_no_equals():
    assert url.parse_query('a=1&foo') == {'a': '1'}


def test_no_value():
    assert url.parse_query('a=') == {'a': ''}


def test_repeated_mixed_with_other_keys():
    assert url.parse_query('a=1&b=2&a=3') == {'a': ['1', '3'], 'b': '2'}
