import re

def special_match(strg, search=re.compile(r'[[&]').search):
    return not bool(search(strg))


special_match