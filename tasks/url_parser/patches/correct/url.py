from utils import unquote


def parse_query(query_string):
    result = {}
    if not query_string:
        return result
    for pair in query_string.split('&'):
        if '=' not in pair:
            continue
        key, value = pair.split('=', 1)
        key = unquote(key)
        value = unquote(value)
        if key in result:
            if not isinstance(result[key], list):
                result[key] = [result[key]]
            result[key].append(value)
        else:
            result[key] = value
    return result
