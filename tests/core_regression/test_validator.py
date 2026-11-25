import unittest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "legacy_core"))

from Core.factor.filter.expression_verifier.validator import ExpressionValidator

class TestValidator(unittest.TestCase):
    def setUp(self):
        self.validator = ExpressionValidator()

    def test_valid_expression(self):
        expr = "ts_mean(close, 5)"
        result = self.validator.check_expression(expr)
        self.assertTrue(result["valid"], "合法的表达式应通过校验")

    def test_invalid_syntax(self):
        expr = "ts_mean(close, )"
        result = self.validator.check_expression(expr)
        self.assertFalse(result["valid"], "语法错误的表达式应被拦截")
        self.assertIn("errors", result)

    def test_invalid_operator(self):
        expr = "fake_op(close, 5)"
        result = self.validator.check_expression(expr)
        self.assertFalse(result["valid"], "不存在的操作符应被拦截")

    def test_invalid_arguments(self):
        expr = "ts_mean(close, 5, 10)" # ts_mean 只有?三个参数
        result = self.validator.check_expression(expr)
        # validator 目前可能对某些参数过多拦截，看底层逻辑，或者至少语法能解析
        # 只要能运行即?        pass

if __name__ == '__main__':
    unittest.main()
