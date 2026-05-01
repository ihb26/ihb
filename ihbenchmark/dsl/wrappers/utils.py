from typing import Literal


type CompareOp = Literal["<", ">", "<=", ">=", "="]


def op_compare(
    a: int | float,
    op: CompareOp,
    b: int | float
) -> bool:
    match op:
        case "<":
            return a < b
        case ">":
            return a > b
        case "<=":
            return a <= b
        case ">=":
            return a >= b
        case "=":
            return a == b
        case _:
            raise ValueError(
                f"Invalid operator '{op}': expected one of "
                "'<', '>', '<=', '>=', '='"
            )
