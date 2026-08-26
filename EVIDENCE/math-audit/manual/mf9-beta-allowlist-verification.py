"""M-F9 / DV-026 remediation verification.

Confirms that adding `beta`, `betainc`, `betainc_regularized` to
math-audit-mcp's ALLOWED_MATH_FUNCTIONS (allowlists.py) resolves the
expression-guard rejection discovered during EMA-005 BETA-SYM-01 claim
authoring.

Three tests:
  1. beta(a,b) == gamma(a)*gamma(b)/gamma(a+b)  [symbolic, reduces to 0]
  2. betainc_regularized(a,b,0,x) + betainc_regularized(b,a,0,1-x) == 1
     [numeric confirmation at a=5, b=0.5, x=0.3]
  3. betainc(a,b,0,x) parses without error

Run:  python EVIDENCE/math-audit/manual/mf9-beta-allowlist-verification.py
Requires: math-audit-mcp src on sys.path (or installed editable).
"""

from __future__ import annotations

import sys

sys.path.insert(0, r"C:\dev\--DEV\Math Audit MCP\src")

from math_audit_mcp.security.expression_guard import safe_sympify
from sympy import N, S, simplify


def test_beta_gamma_identity() -> None:
    lhs = safe_sympify("beta(a,b)", variables=["a", "b"])
    rhs = safe_sympify("gamma(a)*gamma(b)/gamma(a+b)", variables=["a", "b"])
    diff = simplify(lhs - rhs)
    assert diff == 0, f"Expected 0, got {diff}"
    print(f"PASS  beta(a,b) == gamma(a)*gamma(b)/gamma(a+b)  [diff={diff}]")


def test_betainc_regularized_symmetry() -> None:
    lhs = safe_sympify(
        "betainc_regularized(a,b,0,x) + betainc_regularized(b,a,0,1-x)",
        variables=["a", "b", "x"],
    )
    rhs = safe_sympify("1", variables=["a", "b", "x"])
    subs = {S("a"): 5, S("b"): S("0.5"), S("x"): S("0.3")}
    val = N(lhs.subs(subs) - rhs.subs(subs), 15)
    assert abs(complex(val)) < 1e-10, f"Expected ~0, got {val}"
    print(f"PASS  betainc_regularized symmetry  [numeric residual={val}]")


def test_betainc_parses() -> None:
    expr = safe_sympify("betainc(a,b,0,x)", variables=["a", "b", "x"])
    print(f"PASS  betainc(a,b,0,x) parses  [{expr}]")


if __name__ == "__main__":
    test_beta_gamma_identity()
    test_betainc_regularized_symmetry()
    test_betainc_parses()
    print("\nALL 3 TESTS PASSED")
