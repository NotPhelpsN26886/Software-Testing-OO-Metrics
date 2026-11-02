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