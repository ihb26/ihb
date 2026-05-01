from .predicate_types import Context, Predicate, PredicateResult


def AND(*preds: Predicate) -> Predicate:
    """Returns true if all child predicates are true"""
    def _inner(ctx: Context) -> PredicateResult:
        ok, children = True, []
        for pred in preds:
            result = pred(ctx)
            children.append(result)
            if not result.ok:
                ok = False
                break
        return PredicateResult(ok=ok, name="AND", children=children)
    return _inner


def OR(*preds: Predicate) -> Predicate:
    """Returns true if any child predicate is true"""
    def _inner(ctx: Context) -> PredicateResult:
        ok, children = False, []
        for pred in preds:
            result = pred(ctx)
            children.append(result)
            if result.ok:
                ok = True
                break
        return PredicateResult(ok=ok, name="OR", children=children)
    return _inner


def NOT(pred: Predicate) -> Predicate:
    """Returns true if the child predicate is false"""
    def _inner(ctx: Context) -> PredicateResult:
        result = pred(ctx)
        return PredicateResult(ok=(not result.ok), name="NOT", children=[result])
    return _inner
