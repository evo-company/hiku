import re

UPPER_CAMEL_CASE_BOUNDS_RE = re.compile(r"(.)([A-Z][a-z]+)")
LOWER_CAMEL_CASE_BOUNDS_RE = re.compile(r"([a-z0-9])([A-Z])")


# http://stackoverflow.com/a/1176023/1072990
def to_snake_case(name: str) -> str:
    s1 = UPPER_CAMEL_CASE_BOUNDS_RE.sub(r"\1_\2", name)
    return LOWER_CAMEL_CASE_BOUNDS_RE.sub(r"\1_\2", s1).lower()
