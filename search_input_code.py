class ClassInfo:
    def __init__(self, name):
        self.name = name
        self.methods = []       # list of MethodInfo
        self.fields = set()     # instance attributes like self.x

class MethodInfo:
    def __init__(self, name):
        self.name = name
        self.calls = set()     # names of methods invoked
        self.field_accesses = set()  # self.attr names
        self.complexity = 1