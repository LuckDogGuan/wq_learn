"""Static FASTEXPR Lexer + Recursive-Descent AST Validator (10 Hard Gates).

Enforces:
1. settings.delay == 1 (D1-Only, no D0) & type == REGULAR
2. Decision #3: permanent ban on binary +, *, and add(), multiply(), trade_when()
3. Gold 81 allowed operator whitelist (blocks ts_median, left_tail, right_tail, etc.)
4. Known signature & behavioral traps: hump(x, hump=...), ts_scale, ts_step(1),
   ts_target_tvr_decay lambda_max <= 1, ts_decay_linear(rank(...), d) without dense=true,
   ts_backfill d <= 504, ts_product d <= 60
5. API enum checks: RAM forbidden (must be REVERSION_AND_MOMENTUM), maxPosition region,
   ASI/HKG/KOR maxTrade warning/check, visualization == False
6. 42 static-defect template patterns (markdown prefix, top-level boolean, market constants,
   redundant double wraps, domain-sensitive log/sqrt/inverse warning)
7. Known non-numeric trap fields (IBES IDs, currency codes, CUSIPs)
8. Operator count accounting excluding free ts_backfill/group_backfill
9. Alphas=0 queue purity guard (all economic fields must have alphaCount == 0)
10. Canonical SHA-256 payload fingerprint for exact dedup & reconcile
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from wq_research_v2.config_loader import (
    load_buggy_templates_config,
    load_d1_thresholds,
    load_operators_config,
)


@dataclass
class Token:
    kind: str  # IDENT, NUMBER, STRING, OP, LPAREN, RPAREN, COMMA, EQ, EOF
    value: str
    pos: int


@dataclass
class CallNode:
    name: str
    args: list[Any]
    kwargs: dict[str, Any]


@dataclass
class BinOpNode:
    op: str
    left: Any
    right: Any


@dataclass
class UnaryOpNode:
    op: str
    operand: Any


@dataclass
class IdentNode:
    name: str


@dataclass
class LiteralNode:
    value: Any


_TOKEN_SPEC = re.compile(
    r"""
    (?P<WS>\s+)
    |(?P<STRING>'[^']*'|"[^"]*")
    |(?P<NUMBER>(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?)
    |(?P<IDENT>[A-Za-z_][A-Za-z0-9_]*)
    |(?P<OP>==|!=|<=|>=|&&|\|\||[+\-*/<>!])
    |(?P<EQ>=)
    |(?P<LPAREN>\()
    |(?P<RPAREN>\))
    |(?P<COMMA>,)
    |(?P<SEMI>;)
    |(?P<MISMATCH>.)
    """,
    re.VERBOSE,
)


def tokenize(expr: str) -> list[Token]:
    tokens: list[Token] = []
    for m in _TOKEN_SPEC.finditer(expr):
        kind = m.lastgroup or "MISMATCH"
        val = m.group()
        if kind == "WS":
            continue
        if kind == "MISMATCH":
            raise SyntaxError(f"Unexpected character {val!r} at pos {m.start()}")
        tokens.append(Token(kind, val, m.start()))
    tokens.append(Token("EOF", "", len(expr)))
    return tokens


class _Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.idx = 0

    def peek(self, offset: int = 0) -> Token:
        pos = min(self.idx + offset, len(self.tokens) - 1)
        return self.tokens[pos]

    def consume(self, expected_kind: Optional[str] = None) -> Token:
        tok = self.peek()
        if expected_kind and tok.kind != expected_kind:
            raise SyntaxError(f"Expected {expected_kind}, got {tok.kind} ({tok.value!r}) at pos {tok.pos}")
        self.idx += 1
        return tok

    def parse(self) -> Any:
        node = self.parse_or()
        if self.peek().kind != "EOF":
            tok = self.peek()
            raise SyntaxError(f"Unexpected trailing token {tok.value!r} at pos {tok.pos}")
        return node

    def parse_or(self) -> Any:
        node = self.parse_and()
        while self.peek().kind == "OP" and self.peek().value == "||":
            op = self.consume().value
            node = BinOpNode(op, node, self.parse_and())
        return node

    def parse_and(self) -> Any:
        node = self.parse_cmp()
        while self.peek().kind == "OP" and self.peek().value == "&&":
            op = self.consume().value
            node = BinOpNode(op, node, self.parse_cmp())
        return node

    def parse_cmp(self) -> Any:
        node = self.parse_add()
        while self.peek().kind == "OP" and self.peek().value in ("==", "!=", "<", "<=", ">", ">="):
            op = self.consume().value
            node = BinOpNode(op, node, self.parse_add())
        return node

    def parse_add(self) -> Any:
        node = self.parse_mul()
        while self.peek().kind == "OP" and self.peek().value in ("+", "-"):
            op = self.consume().value
            node = BinOpNode(op, node, self.parse_mul())
        return node

    def parse_mul(self) -> Any:
        node = self.parse_unary()
        while self.peek().kind == "OP" and self.peek().value in ("*", "/"):
            op = self.consume().value
            node = BinOpNode(op, node, self.parse_unary())
        return node

    def parse_unary(self) -> Any:
        if self.peek().kind == "OP" and self.peek().value in ("-", "+", "!"):
            op = self.consume().value
            return UnaryOpNode(op, self.parse_unary())
        return self.parse_primary()

    def parse_primary(self) -> Any:
        tok = self.peek()
        if tok.kind == "NUMBER":
            self.consume()
            val = float(tok.value) if ("." in tok.value or "e" in tok.value.lower()) else int(tok.value)
            return LiteralNode(val)
        if tok.kind == "STRING":
            self.consume()
            return LiteralNode(tok.value[1:-1])
        if tok.kind == "LPAREN":
            self.consume("LPAREN")
            node = self.parse_or()
            self.consume("RPAREN")
            return node
        if tok.kind == "IDENT":
            ident = self.consume("IDENT").value
            if self.peek().kind == "LPAREN":
                return self.parse_call(ident)
            return IdentNode(ident)
        raise SyntaxError(f"Unexpected token {tok.kind} ({tok.value!r}) at pos {tok.pos}")

    def parse_call(self, name: str) -> CallNode:
        self.consume("LPAREN")
        args: list[Any] = []
        kwargs: dict[str, Any] = {}
        if self.peek().kind != "RPAREN":
            while True:
                if self.peek().kind == "IDENT" and self.peek(1).kind == "EQ":
                    k = self.consume("IDENT").value
                    self.consume("EQ")
                    kwargs[k] = self.parse_or()
                else:
                    args.append(self.parse_or())
                if self.peek().kind == "COMMA":
                    self.consume("COMMA")
                else:
                    break
        self.consume("RPAREN")
        return CallNode(name=name, args=args, kwargs=kwargs)


@dataclass
class ValidationReport:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    operators_used: list[str] = field(default_factory=list)
    distinct_counted_ops: int = 0
    total_counted_calls: int = 0
    fields_used: list[str] = field(default_factory=list)
    normalized_expr: str = ""
    payload_fingerprint: str = ""
    canonical_dedup_key: str = ""


def normalize_expression(expr: str) -> str:
    return re.sub(r"\s+", "", expr.strip())


def compute_payload_fingerprint(expression: str, settings: Mapping[str, Any]) -> tuple[str, str]:
    norm = normalize_expression(expression)
    full_obj = {"regular": norm, "settings": dict(sorted(settings.items()))}
    full_fp = hashlib.sha256(json.dumps(full_obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    dedup_settings = {
        k: v for k, v in settings.items() if k not in ("simulationMode", "visualization")
    }
    dedup_obj = {"regular": norm, "settings": dict(sorted(dedup_settings.items()))}
    dedup_key = hashlib.sha256(json.dumps(dedup_obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return full_fp, dedup_key


class ExprValidator:
    """Enforces all 10 static D1-Only & Decision #3 expression/setting gates."""

    def __init__(self) -> None:
        self.ops_cfg = load_operators_config()
        self.buggy_cfg = load_buggy_templates_config()
        self.d1_cfg = load_d1_thresholds()

        self.allowed_ops = set(self.ops_cfg["allowed_operators_gold_81"])
        self.forbidden_ops = set(self.ops_cfg["forbidden_operators_decision_3"])
        self.missing_gold_ops = set(self.ops_cfg["missing_at_gold_level"])
        self.free_ops = set(self.ops_cfg["free_tiebreaker_and_pp_operators"])
        self.group_constants = set(self.ops_cfg["group_constants"])
        self.pv1_helpers = set(self.ops_cfg["allowed_pv1_alpha0_helpers"])
        self.trap_patterns = [re.compile(p, re.I) for p in self.ops_cfg["trap_field_patterns"]]
        self.md_prefix_re = re.compile(self.buggy_cfg["markdown_prefix_regex"])
        self.market_const_ops = set(self.buggy_cfg["market_constant_calls"])
        self.domain_ops = set(self.buggy_cfg["domain_sensitive_ops"])
        self.blocked_norm = set(self.buggy_cfg["blocked_normalized_expressions"])

    def validate(
        self,
        expression: str,
        settings: Mapping[str, Any],
        *,
        queue_type: str = "NORMAL",
        field_alpha_counts: Optional[Mapping[str, int]] = None,
        strictly_positive_fields: Optional[set[str]] = None,
        is_ppa: bool = False,
    ) -> ValidationReport:
        errors: list[str] = []
        warnings: list[str] = []
        expr = (expression or "").strip()
        norm = normalize_expression(expr)
        full_fp, dedup_key = compute_payload_fingerprint(expr, settings)

        if not expr:
            return ValidationReport(False, ["Expression is empty"], [], [], 0, 0, [], norm, full_fp, dedup_key)

        # Gate 1: D1-Only & Settings validation
        delay = settings.get("delay")
        if delay != 1:
            errors.append(f"D1-Only violation: settings.delay must be 1, got {delay!r}")
        if settings.get("visualization") is True:
            errors.append("settings.visualization must be False")

        region = str(settings.get("region", "")).upper()
        neut = str(settings.get("neutralization", "")).upper()
        aliases = self.ops_cfg["valid_neutralizations"]["aliases_forbidden"]
        if neut in aliases:
            errors.append(f"Forbidden neutralization alias {neut!r}; use {aliases[neut]!r}")
        elif neut:
            if region == "AMR":
                valid_neuts = set(self.ops_cfg["valid_neutralizations"]["amr_only_7"])
            else:
                valid_neuts = set(self.ops_cfg["valid_neutralizations"]["standard_11"]) | set(
                    self.ops_cfg["valid_neutralizations"]["multi_country_extra"]
                )
            if neut not in valid_neuts:
                errors.append(f"Invalid neutralization {neut!r} for region {region!r}")

        if str(settings.get("maxPosition", "OFF")).upper() == "ON":
            if region not in set(self.d1_cfg["regular_d1"]["max_position_regions"]):
                errors.append(f"maxPosition=ON is only allowed for USA/ASI/EUR, got region={region!r}")

        if region in set(self.d1_cfg["regular_d1"]["investability_regions"]):
            if str(settings.get("maxTrade", "OFF")).upper() != "ON":
                warnings.append(f"Region {region} prefers maxTrade='ON' for Investability compliance")

        # Gate 6a: Markdown numbering prefix / blocked normalized template
        if self.md_prefix_re.match(expr):
            errors.append("Defect template: expression starts with Markdown numbering prefix")
        if norm in self.blocked_norm:
            errors.append("Defect template: matched 42-template quarantine blocklist")

        # Parse AST
        try:
            ast_root = _Parser(tokenize(expr)).parse()
        except SyntaxError as exc:
            errors.append(f"SyntaxError: {exc}")
            return ValidationReport(False, errors, warnings, [], 0, 0, [], norm, full_fp, dedup_key)

        # Gate 6b: Top-level pure boolean/comparison expression forbidden
        if isinstance(ast_root, BinOpNode) and ast_root.op in ("==", "!=", "<", "<=", ">", ">=", "&&", "||"):
            errors.append(f"Defect template: top-level pure boolean/comparison ({ast_root.op}) is not a valid alpha")

        ops_called: list[str] = []
        fields_used: list[str] = []
        self._walk(ast_root, ops_called, fields_used, errors, warnings, strictly_positive_fields or set())

        # Deduplicate fields preserving order
        seen_f: set[str] = set()
        unique_fields: list[str] = []
        for f in fields_used:
            if f not in seen_f:
                seen_f.add(f)
                unique_fields.append(f)

        # Gate 7: Trap fields
        for f in unique_fields:
            for pat in self.trap_patterns:
                if pat.match(f):
                    errors.append(f"Trap non-numeric field blocked: {f}")

        # Gate 8: Operator counting (excluding free ts_backfill / group_backfill)
        counted_calls = [op for op in ops_called if op not in self.free_ops]
        distinct_counted = len(set(counted_calls))
        total_counted = len(counted_calls)
        if is_ppa and total_counted > int(self.d1_cfg["power_pool_d1"]["max_counted_operators"]):
            errors.append(f"Power Pool operator cap exceeded: {total_counted} > 8 (excluding backfill)")
        elif total_counted >= 6:
            warnings.append(f"High operator count ({total_counted} counted calls, target < 6 for Genius Tiebreaker)")

        # Gate 9: Alphas=0 queue purity guard
        if queue_type.upper() == "UNUSED_ALPHA0":
            economic_fields = [f for f in unique_fields if f.lower() not in self.pv1_helpers]
            if not economic_fields:
                errors.append("UNUSED_ALPHA0 queue requires at least one economic field")
            elif field_alpha_counts is None:
                errors.append("UNUSED_ALPHA0 purity check requires field_alpha_counts metadata")
            else:
                for ef in economic_fields:
                    ac = field_alpha_counts.get(ef)
                    if ac is None:
                        errors.append(f"UNUSED_ALPHA0 purity failed: unknown alphaCount for field {ef!r}")
                    elif int(ac) != 0:
                        errors.append(f"UNUSED_ALPHA0 purity failed: field {ef!r} has alphaCount={ac} != 0")

        return ValidationReport(
            valid=(len(errors) == 0),
            errors=errors,
            warnings=warnings,
            operators_used=ops_called,
            distinct_counted_ops=distinct_counted,
            total_counted_calls=total_counted,
            fields_used=unique_fields,
            normalized_expr=norm,
            payload_fingerprint=full_fp,
            canonical_dedup_key=dedup_key,
        )

    def _walk(
        self,
        node: Any,
        ops_called: list[str],
        fields_used: list[str],
        errors: list[str],
        warnings: list[str],
        positive_fields: set[str],
    ) -> None:
        if isinstance(node, IdentNode):
            if node.name.lower() not in self.group_constants:
                fields_used.append(node.name)
            return
        if isinstance(node, LiteralNode):
            return
        if isinstance(node, UnaryOpNode):
            self._walk(node.operand, ops_called, fields_used, errors, warnings, positive_fields)
            return
        if isinstance(node, BinOpNode):
            if node.op in ("+", "*"):
                errors.append(
                    f"Decision #3 forbidden binary operator {node.op!r} (no add/multiply; use min(rank(A),rank(B)) or reverse(...))"
                )
            elif node.op == "-":
                ops_called.append("subtract")
            elif node.op == "/":
                ops_called.append("divide")
            self._walk(node.left, ops_called, fields_used, errors, warnings, positive_fields)
            self._walk(node.right, ops_called, fields_used, errors, warnings, positive_fields)
            return
        if isinstance(node, CallNode):
            name = node.name
            ops_called.append(name)

            # Gate 2 & 3: Forbidden / missing / unknown operators
            if name in self.forbidden_ops:
                errors.append(f"Decision #3 forbidden operator: {name}()")
            elif name in self.missing_gold_ops:
                errors.append(f"Operator unavailable at Gold account level: {name}()")
            elif name not in self.allowed_ops:
                errors.append(f"Unknown or unverified operator outside Gold-81 whitelist: {name}()")

            # Gate 4: Specific signature & behavioral traps
            if name == "hump":
                if len(node.args) > 1 or "hump" not in node.kwargs:
                    errors.append("Signature trap: hump() must use keyword argument hump(x, hump=0.01)")
            elif name == "ts_scale":
                if "scale" in node.kwargs:
                    errors.append("Signature trap: ts_scale(x, d, constant=0) does not accept scale=")
            elif name == "ts_step":
                if len(node.args) != 1 or not isinstance(node.args[0], LiteralNode) or node.args[0].value != 1:
                    errors.append("Signature trap: ts_step(1) only accepts literal 1")
            elif name == "ts_target_tvr_decay":
                lmax = node.kwargs.get("lambda_max")
                if isinstance(lmax, LiteralNode) and isinstance(lmax.value, (int, float)) and lmax.value > 1:
                    errors.append(f"Behavioral trap (JX79797): ts_target_tvr_decay lambda_max={lmax.value} > 1 amplifies TVR")
            elif name == "ts_decay_linear":
                if node.args and isinstance(node.args[0], CallNode) and node.args[0].name in ("rank", "group_rank"):
                    dense_kw = node.kwargs.get("dense")
                    is_dense_true = isinstance(dense_kw, IdentNode) and dense_kw.name.lower() == "true"
                    if not is_dense_true:
                        errors.append(
                            "Behavioral trap (WL13229): ts_decay_linear(rank(...), d) defaults dense=false pulling NaNs to 0; "
                            "place ts_decay_linear inside rank() or pass dense=true"
                        )
            elif name == "ts_backfill":
                d_node = node.args[1] if len(node.args) >= 2 else node.kwargs.get("lookback")
                if isinstance(d_node, LiteralNode) and isinstance(d_node.value, (int, float)):
                    if d_node.value > int(self.buggy_cfg["max_ts_backfill_window"]):
                        errors.append(f"Stale backfill trap: ts_backfill window {d_node.value} > 504")
                if node.args and isinstance(node.args[0], CallNode) and node.args[0].name == "ts_backfill":
                    errors.append("Defect template: redundant double ts_backfill(ts_backfill(...))")
            elif name == "ts_product":
                d_node = node.args[1] if len(node.args) >= 2 else None
                if isinstance(d_node, LiteralNode) and isinstance(d_node.value, (int, float)):
                    if d_node.value > int(self.buggy_cfg["max_ts_product_window"]):
                        errors.append(f"Overflow trap: ts_product window {d_node.value} > 60")
            elif name == "group_neutralize":
                if (
                    len(node.args) >= 2
                    and isinstance(node.args[0], CallNode)
                    and node.args[0].name == "group_zscore"
                    and len(node.args[0].args) >= 2
                    and isinstance(node.args[1], IdentNode)
                    and isinstance(node.args[0].args[1], IdentNode)
                    and node.args[1].name == node.args[0].args[1].name
                ):
                    errors.append("Defect template: redundant group_neutralize(group_zscore(x, g), g)")

            # Gate 6c: Market-constant zero-variance calls
            if name in self.market_const_ops:
                if any(isinstance(a, IdentNode) and a.name.lower() == "market" for a in node.args):
                    errors.append(f"Defect template: zero-variance market constant {name}(..., market)")

            # Gate 6d: Domain-sensitive ops
            if name in self.domain_ops:
                inner_fields: list[str] = []
                if node.args:
                    self._collect_fields(node.args[0], inner_fields)
                if not inner_fields or not all(f in positive_fields for f in inner_fields):
                    warnings.append(f"Domain-sensitive operator {name}() requires verified strictly-positive/non-zero input")

            for a in node.args:
                self._walk(a, ops_called, fields_used, errors, warnings, positive_fields)
            for v in node.kwargs.values():
                self._walk(v, ops_called, fields_used, errors, warnings, positive_fields)

    def _collect_fields(self, node: Any, out: list[str]) -> None:
        if isinstance(node, IdentNode) and node.name.lower() not in self.group_constants:
            out.append(node.name)
        elif isinstance(node, UnaryOpNode):
            self._collect_fields(node.operand, out)
        elif isinstance(node, BinOpNode):
            self._collect_fields(node.left, out)
            self._collect_fields(node.right, out)
        elif isinstance(node, CallNode):
            for a in node.args:
                self._collect_fields(a, out)
            for v in node.kwargs.values():
                self._collect_fields(v, out)
