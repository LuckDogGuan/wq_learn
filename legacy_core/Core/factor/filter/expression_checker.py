import sys
import os
import json
from pathlib import Path
from typing import Union, List, Dict, Any

# 将 validator.py 所在的目录加入路径，否则其中的 parsetab.py 等可能会报错
current_dir = Path(__file__).parent
verifier_dir = current_dir / "expression_verifier"
if str(verifier_dir) not in sys.path:
    sys.path.insert(0, str(verifier_dir))

try:
    from validator import ExpressionValidator
except ImportError as e:
    print(f"载入 ExpressionValidator 失败: {e}")
    ExpressionValidator = None


def verify_alpha_expression(expression: str) -> Dict[str, Any]:
    """
    单个 Alpha 表达式的语法合法性校验。
    
    参数:
        expression (str): 待校验的表达式，如 "rank(close) > 0.5"
    
    返回:
        Dict: 包含 'valid' (bool), 'errors' (list) 等详细结果的字典。
    """
    if ExpressionValidator is None:
        return {"valid": False, "errors": ["语法验证器未成功加载。"]}
    
    try:
        validator = ExpressionValidator()
        result = validator.check_expression(expression)
        return result
    except Exception as e:
        return {"valid": False, "errors": [f"校验过程发生异常: {str(e)}"]}


def batch_verify_expressions(expressions: List[str]) -> List[Dict[str, Any]]:
    """
    批量 Alpha 表达式的语法合法性校验。
    
    参数:
        expressions (List[str]): 待校验的表达式列表。
        
    返回:
        List[Dict]: 每个表达式对应的详细校验结果列表。
    """
    if ExpressionValidator is None:
        return [{"valid": False, "errors": ["语法验证器未成功加载。"]} for _ in expressions]
    
    validator = ExpressionValidator()
    results = []
    for expr in expressions:
        try:
            res = validator.check_expression(expr)
            # 添加原表达式以方便对应
            res["expression"] = expr
            results.append(res)
        except Exception as e:
            results.append({"valid": False, "errors": [f"校验异常: {str(e)}"], "expression": expr})
            
    return results

