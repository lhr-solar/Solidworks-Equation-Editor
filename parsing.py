import re

LINE_RE = re.compile(r'^\s*"(?P<var>.+?)"\s*=\s*(?P<expr>.+?)\s*$')


def parse_equations(text: str):
    equations = []
    for i, line in enumerate(text.splitlines()):
        line = line.strip()
        if not line:
            continue
        m = LINE_RE.match(line)
        if not m:
            continue
        equations.append({
            'name': m.group('var'),
            'expr': m.group('expr'),
            'line_index': i,
        })
    return equations


def serialize_equations(eqs):
    lines = []
    for e in eqs:
        lines.append(f"\"{e['name']}\"= {e['expr']}")
    return '\n'.join(lines) + '\n'
