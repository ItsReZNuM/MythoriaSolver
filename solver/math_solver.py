import ast
import operator
from typing import List, Dict, Any, Union

# Allowed operators mapping
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


class MathSolver:
    """
    Safely solves arithmetic equations using Python's AST without eval().
    Example:
        '-10 * -2 - (-2) + 0' -> '22'
        '4 * 8 * 3 - 8' -> '88'
        '-4 - (-6) + (-9) - (-1)' -> '-6'
        '2 + 0 * 5 - 2' -> '0'
    """

    def _eval_node(self, node: ast.AST) -> Union[int, float]:
        if isinstance(node, ast.Expression):
            return self._eval_node(node.body)

        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Unsupported constant type: {type(node.value)}")

        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type in OPERATORS:
                operand = self._eval_node(node.operand)
                return OPERATORS[op_type](operand)
            raise ValueError(f"Unsupported unary operator: {op_type}")

        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type in OPERATORS:
                left = self._eval_node(node.left)
                right = self._eval_node(node.right)
                return OPERATORS[op_type](left, right)
            raise ValueError(f"Unsupported binary operator: {op_type}")

        else:
            raise ValueError(f"Disallowed AST node: {type(node)}")

    def solve(self, question: str, limit: int = 1) -> List[Dict[str, Any]]:
        clean_q = question.strip()
        if not clean_q:
            return []

        try:
            tree = ast.parse(clean_q, mode="eval")
            val = self._eval_node(tree)

            # If float is effectively integer, format as int
            if isinstance(val, float) and val.is_integer():
                val = int(val)

            ans_str = str(val)
            return [
                {
                    "answer": ans_str,
                    "score": 100.0,
                    "type": "math_evaluation",
                }
            ]
        except Exception:
            return []

    def close(self):
        pass
