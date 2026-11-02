import ast
import json
import sys

try:
    from input_normalization import normalize_python_source, parse_python
except ImportError:
    import re

    def normalize_python_source(source: str) -> str:
        lines = source.splitlines(True)
        out = []
        for line in lines:
            m = re.match(r'^[ \t]*', line)
            indent = m.group(0)
            rest = line[len(indent):]
            out.append(indent.expandtabs(4) + rest)
        return ''.join(out)

    def parse_python(source: str):
        normalized = normalize_python_source(source)
        try:
            return ast.parse(normalized)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python indentation/syntax: {e}") from e


class MethodInfo:
    def __init__(self, name, node):
        self.name = name
        self.node = node
        self.calls = set()
        self.field_accesses = set()
        self.complexity = method_complexity(node)


class ClassInfo:
    def __init__(self, name):
        self.name = name
        self.methods = []
        self.fields = set()


def method_complexity(fn_ast):
    complexity = 1
    for node in ast.walk(fn_ast):
        if isinstance(node, (
            ast.If, ast.For, ast.While, ast.AsyncFor,
            ast.With, ast.AsyncWith, ast.Try, ast.ExceptHandler,
            ast.BoolOp, ast.Compare, ast.IfExp, ast.Assert
        )):
            complexity += 1
    return complexity


def compute_wmc(class_info):
    return sum(method.complexity for method in class_info.methods)


def compute_lcom(class_info):
    methods = class_info.methods
    if len(methods) < 2:
        return 0

    pairs = 0
    connected = 0
    for i in range(len(methods)):
        for j in range(i + 1, len(methods)):
            pairs += 1
            a = methods[i].field_accesses
            b = methods[j].field_accesses
            if a & b:
                connected += 1
    unconnected = pairs - connected
    return max(0, unconnected - connected)


def compute_coupling_between(class_a, class_b):
    edges = set()
    for method in class_a.methods:
        for call in method.calls:
            if call == class_b.name:
                edges.add(("call", call))
        for field in method.field_accesses:
            if field in class_b.fields:
                edges.add(("field", field))
    return len(edges)


def compute_rfc(class_info):
    response = set()
    queue = [m.name for m in class_info.methods]

    while queue:
        name = queue.pop()
        if name in response:
            continue
        response.add(name)

        method_map = {m.name: m for m in class_info.methods}
        if name in method_map:
            for called in method_map[name].calls:
                if called not in response:
                    queue.append(called)

    return len(response)


def collect_project_metrics(source):
    tree = parse_python(source)
    classes = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_info = ClassInfo(node.name)
            classes[node.name] = class_info

            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method = MethodInfo(item.name, item)
                    class_info.methods.append(method)

                    for child in ast.walk(item):
                        if isinstance(child, ast.Call):
                            func = child.func
                            if isinstance(func, ast.Attribute):
                                if isinstance(func.value, ast.Name) and func.value.id == 'self':
                                    method.calls.add(func.attr)
                            elif isinstance(func, ast.Name):
                                method.calls.add(func.id)

                        if isinstance(child, ast.Attribute):
                            if isinstance(child.value, ast.Name) and child.value.id == 'self':
                                method.field_accesses.add(child.attr)

                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                            class_info.fields.add(target.attr)

    results = {}
    for class_name, class_info in classes.items():
        coupled = {}
        for other_name, other_class in classes.items():
            if other_name != class_name:
                coupled[other_name] = compute_coupling_between(class_info, other_class)

        results[class_name] = {
            'WMC': compute_wmc(class_info),
            'LCOM': compute_lcom(class_info),
            'RFC': compute_rfc(class_info),
            'COUPLING': coupled
        }

    return results


def main():
    source = sys.stdin.read()

    try:
        normalized = normalize_python_source(source)
        results = collect_project_metrics(normalized)
        output = {
            'success': True,
            'results': results
        }
        print(json.dumps(output))
    except Exception as exc:
        print(json.dumps({
            'success': False,
            'error': f'Invalid Python indentation or syntax: {exc}'
        }))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
