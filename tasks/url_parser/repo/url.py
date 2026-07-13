from utils import unquote


def parse_query(query_string):
    result = {}
    if not query_string:
        return result
    for pair in query_string.split('&'):
        if '=' not in pair:
            continue
        key, value = pair.split('=', 1)
        result[key] = unquote(value)
    return result
