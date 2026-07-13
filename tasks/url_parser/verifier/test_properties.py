from hypothesis import given, strategies as st
from urllib.parse import parse_qs
import url


ALPHANUM_SPACE = 'abcdefghijklmnopqrstuvwxyz0123456789 '


def _normalize(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


@st.composite
def query_string(draw):
    key = st.text(alphabet=ALPHANUM_SPACE, min_size=1, max_size=10)
    value = st.text(alphabet=ALPHANUM_SPACE, min_size=0, max_size=10)
    pairs = draw(st.lists(st.tuples(key, value), min_size=0, max_size=20))
    encoded = [f'{k.replace(" ", "+")}={v.replace(" ", "+")}' for k, v in pairs]
    return '&'.join(encoded)


@given(query=query_string())
def test_parse_query_matches_standard(query):
    expected = parse_qs(query, keep_blank_values=True, separator='&')
    actual = url.parse_query(query)
    normalized = {k: _normalize(v) for k, v in actual.items()}
    assert normalized == expected


@given(
    s=st.text(alphabet=ALPHANUM_SPACE, min_size=0, max_size=50),
    t=st.text(alphabet=ALPHANUM_SPACE, min_size=0, max_size=50),
)
def test_unquote_decodes_plus(s, t):
    encoded = s.replace(' ', '+') + '+' + t.replace(' ', '+')
    assert url.unquote(encoded) == s + ' ' + t
