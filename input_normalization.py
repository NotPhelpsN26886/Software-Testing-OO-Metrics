import ast
import re

def normalize_python_source(source: str) -> str:
    lines = source.splitlines(True)
    out = []
    for line in lines:
        m = re.match(r'^[ \t]*', line)
        indent = m.group(0)
        rest = line[len(indent):]
        out.append(indent.expandtabs(4) + rest)
    return "".join(out)

def parse_python(source: str):
    normalized = normalize_python_source(source)
    try:
        return ast.parse(normalized)
    except SyntaxError as e:
        raise ValueError(f"Invalid Python indentation/syntax: {e}") from e