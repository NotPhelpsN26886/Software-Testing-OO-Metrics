def compute_coupling_between(class_a, class_b):
    edges = set()
    for method in class_a.methods:
        for call in method.calls:
            # if call target is known to be class_b, add an edge
            if call == class_b.name:
                edges.add(("call", call))
        for field in method.field_accesses:
            # if field belongs to class_b, add edge
            if field in class_b.fields:
                edges.add(("field", field))
    return len(edges)