"""
单元测试：全面校验 unused_alpha_templates 中每一个函数生成的表达式
确保 100% 通过 Brain PLY 语法解析器的 AST 校验。
"""

import sys
import os
import inspect
from pathlib import Path

# 添加工具目录
current_dir = Path(__file__).resolve().parent
workspace_root = current_dir.parent.parent.parent
sys.path.insert(0, str(workspace_root / "tools"))
sys.path.insert(0, str(current_dir))

from Core.factor.filter.expression_verifier.validator import ExpressionValidator
import unused_alpha_templates as uat

def run_tests():
    validator = ExpressionValidator()
    print("=" * 60)
    print("Beginning AST validation for factor/templates/unused functions...")
    print("=" * 60)
    
    all_funcs = [
        obj for name, obj in inspect.getmembers(uat)
        if inspect.isfunction(obj) and obj.__module__ == uat.__name__
    ]
    
    print(f"Total template functions found: {len(all_funcs)}\n")
    
    passed_count = 0
    failed_count = 0
    
    for func in sorted(all_funcs, key=lambda f: f.__name__):
        func_name = func.__name__
        try:
            expr = func()
            res = validator.check_expression(expr)
            if res['valid']:
                print(f" [PASS] {func_name}")
                print(f"        -> {expr}")
                passed_count += 1
            else:
                print(f" [FAIL] {func_name}")
                print(f"        -> {expr}")
                print(f"        -> Errors: {res['errors']}")
                failed_count += 1
        except Exception as e:
            print(f" [EXCP] {func_name} execution error: {e}")
            failed_count += 1
            
    print("\n" + "=" * 60)
    print(f" Summary: Total={len(all_funcs)}, PASS={passed_count}, FAIL={failed_count}")
    print("=" * 60)
    
    return failed_count == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
