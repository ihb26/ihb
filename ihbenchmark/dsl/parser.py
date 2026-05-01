import ast
from typing import Any

from .predicates import FUNCTIONS
from .predicates.predicate_types import Predicate


def _parse_literal(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    
    if isinstance(node, ast.Dict):
        return {
            _parse_literal(k): _parse_literal(v)
            for k, v in zip(node.keys, node.values)
        }
    
    if isinstance(node, (ast.List, ast.Set, ast.Tuple)):
        items = [_parse_literal(e) for e in node.elts]
        if isinstance(node, ast.List):
            return items
        if isinstance(node, ast.Set):
            return set(items)
        if isinstance(node, ast.Tuple):
            return tuple(items)
    
    raise ValueError(f"Unsupported literal in expression: {ast.dump(node)}")


def _parse_predicate(node: ast.AST) -> Predicate:
    if not isinstance(node, ast.Call):
        raise ValueError("Top-level expression must be a function call")
    
    if not isinstance(node.func, ast.Name):
        raise ValueError("Only simple function calls allowed")
    
    name = node.func.id
    if name not in FUNCTIONS:
        raise ValueError(f"Function {name!r} not allowed")
    
    func = FUNCTIONS[name]
    args: list[Any] = []
    for arg in node.args:
        if isinstance(arg, ast.Call):
            args.append(_parse_predicate(arg))
        else:
            args.append(_parse_literal(arg))
    
    if node.keywords:
        raise ValueError("Keyword arguments not allowed")

    pred = func(*args)
    if not callable(pred):
        raise ValueError(f"Function {name!r} did not return predicate")

    return pred


def parse_predicate(expr: str) -> Predicate:
    tree = ast.parse(expr, mode="eval")
    return _parse_predicate(tree.body)
