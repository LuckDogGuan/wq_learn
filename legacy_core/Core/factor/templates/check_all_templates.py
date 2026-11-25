import os
import sys
import glob
import importlib.util
import inspect
import re
import ast
import traceback
from pathlib import Path

base_dir = Path(os.path.abspath(__file__)).parent.parent.parent.parent
sys.path.insert(0, str(base_dir))

# 引入之前的 AST 语法检查模块
try:
    from Core.factor.filter.expression_verifier.validator import ExpressionValidator
    has_validator = True
except ImportError:
    has_validator = False

# 引入平台 API 模块用于查权限
try:
    from Core.api.auth import login
    has_platform_api = True
except ImportError:
    has_platform_api = False


def extract_calls(expr_str):
    calls = set()
    try:
        # 替换 f-string 中的占位符为通用标识符
        expr_str = re.sub(r'\{[^\}]+\}', 'dummy_field', expr_str)
        tree = ast.parse(expr_str, mode='eval')
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                calls.add(node.func.id)
    except Exception:
        pass
    return calls


def main():
    print("="*60)
    print(" 开始本地模板全量校验 (格式 + 平台算子权限)")
    print("="*60)
    
    # 1. 尝试从平台拉取真实算子白名单
    allowed_ops = set()
    if has_platform_api:
        print("[Auth] 正在登录平台并拉取当前用户的可用算子白名单...")
        client = login()
        if client:
            resp = client.get('/operators')
            if resp and resp.status_code == 200:
                data = resp.json()
                if 'results' in data:
                    allowed_ops = {op['name'] for op in data['results']}
                elif isinstance(data, list):
                    allowed_ops = {op['name'] for op in data}
                print(f"[Auth] 成功获取平台算子数量: {len(allowed_ops)} 个")
            else:
                print("[Auth] 无法获取算子列表 (非 200 响应)")
        else:
            print("[Auth] 平台登录失败，跳过在线权限校验。")
    
    # 常见数据字段和非常规标识，不纳入算子权限审核
    data_fields = {'close', 'open', 'high', 'low', 'volume', 'returns', 'vwap', 
                   'cap', 'industry', 'sector', 'subindustry', 'dummy_field'}

    if has_validator:
        validator = ExpressionValidator()
    
    templates_dir = Path(__file__).parent
    py_files = templates_dir.glob("*.py")
    
    total_templates = 0
    passed_templates = 0
    
    failed_syntax = []
    failed_permissions = []
    
    for py_file in py_files:
        module_name = py_file.stem
        # 跳过本文件或辅助文件
        if module_name in ('check_all_templates', '__init__', 'check_perms'):
            continue
            
        print(f"\n>> 正在检查文件: {module_name}.py")
        
        spec = importlib.util.spec_from_file_location(module_name, py_file)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"  [载入错误] {module_name}.py: {e}")
            continue
            
        functions = [f for name, f in inspect.getmembers(module, inspect.isfunction) 
                     if f.__module__ == module_name]
                     
        for func in functions:
            total_templates += 1
            func_name = func.__name__
            sig = inspect.signature(func)
            
            kwargs = {}
            for param_name, param in sig.parameters.items():
                if param.default != inspect.Parameter.empty:
                    kwargs[param_name] = param.default
                elif param_name == 'field' or param_name.startswith('field'):
                    kwargs[param_name] = 'close'
                elif param_name == 'condition':
                    kwargs[param_name] = 'returns > 0'
                elif param_name == 'group':
                    kwargs[param_name] = 'industry'
                elif param_name == 'alpha':
                    kwargs[param_name] = 'close'
                else:
                    kwargs[param_name] = 10
                    
            try:
                expr = func(**kwargs)
                if not isinstance(expr, str):
                    continue
            except Exception as e:
                failed_syntax.append(f"[{module_name}.{func_name}]: 运行时抛错 {e}")
                continue
                
            # 1. 语法检查 (AST本地校验)
            is_syntax_ok = True
            if has_validator:
                result = validator.check_expression(expr)
                is_valid = result.get("valid", False)
                reason = result.get("errors", [])
                if not is_valid:
                    failed_syntax.append(f"[{module_name}.{func_name}]: 语法错误 -> {reason} | 生成的表达式: {expr}")
                    is_syntax_ok = False
            
            # 2. 权限检查
            is_perm_ok = True
            if allowed_ops:
                calls = extract_calls(expr)
                unauthorized = [op for op in calls if op not in allowed_ops and op not in data_fields]
                if unauthorized:
                    failed_permissions.append(f"[{module_name}.{func_name}]: 无权限算子 -> {unauthorized} | 生成的表达式: {expr}")
                    is_perm_ok = False
            
            if is_syntax_ok and is_perm_ok:
                passed_templates += 1

    print("\n" + "="*60)
    print(" 校验报告摘要")
    print("="*60)
    print(f"总计检查模板数: {total_templates}")
    print(f"完全通过模板数: {passed_templates}")
    
    if failed_permissions:
        print("\n[!] 以下模板使用了当前账户无权限的算子:")
        for item in failed_permissions:
            print("  -", item)
    elif allowed_ops:
        print("\n[+] 权限校验通过: 没有发现任何越权使用的算子！")
        
    if failed_syntax:
        print("\n[!] 以下模板存在格式或语法问题:")
        for item in failed_syntax:
            print("  -", item)
    else:
        print("\n[+] 语法校验通过: 所有表达式均符合要求！")


if __name__ == "__main__":
    main()
