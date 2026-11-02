import ast

def instance_field_names(node):
    fields = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "self":
            fields.add(n.attr)
    return fields

def compute_lcom(class_info):
    methods = class_info.methods
    pairs = 0
    connected = 0
    for i in range(len(methods)):
        for j in range(i+1, len(methods)):
            pairs += 1
            a = methods[i].field_accesses
            b = methods[j].field_accesses
            if a & b:
                connected += 1
    unconnected = pairs - connected
    return max(0, unconnected - connected)