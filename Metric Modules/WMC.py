import ast

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