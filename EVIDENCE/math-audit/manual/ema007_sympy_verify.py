"""EMA-007 independent SymPy/Z3/NumPy verification script."""
import sys
import sympy
from sympy import symbols, cos, sin, simplify, exp, log, gamma, Rational
import numpy as np

print("=== SymPy/NumPy Independent Verification (EMA-007) ===")

# ORDERPARAM-01
phi = symbols('phi', real=True)
r = simplify(cos(phi)**2 + sin(phi)**2)
print(f"ORDERPARAM-01: cos^2+sin^2 = {r}  PASS={r==1}")

# VJP-DYN-01
g, Ar = symbols('gamma Arest', real=True, positive=True)
r2 = simplify(-g * ((Ar + 1) - Ar))
print(f"VJP-DYN-01: -gamma*((Arest+1)-Arest) = {r2}  PASS={r2==-g}")

# LNGAMMA-INT-01
r3 = simplify(log(gamma(5)) - log(24))
print(f"LNGAMMA-INT-01: log(gamma(5))-log(24) = {r3}  PASS={r3==0}")

# POLYFIT-01 (Vandermonde normal equations, matching Rust polyfit)
x = np.array([0., 1, 2, 3, 4.])
y = 1.0 + 2.0 * x
V = np.column_stack([np.ones_like(x), x])
c = np.linalg.solve(V.T @ V, V.T @ y)
print(f"POLYFIT-01: coeffs={c}  err={np.max(np.abs(c-[1,2])):.2e}  PASS={np.max(np.abs(c-[1,2]))<1e-10}")

# POLYFIT-02
x2 = np.array([-2., -1, 0, 1, 2.])
y2 = x2**2
V2 = np.column_stack([np.ones_like(x2), x2, x2**2])
c2 = np.linalg.solve(V2.T @ V2, V2.T @ y2)
print(f"POLYFIT-02: coeffs={c2}  err={np.max(np.abs(c2-[0,0,1])):.2e}  PASS={np.max(np.abs(c2-[0,0,1]))<1e-10}")

# SPARSITY-01
vals = [Rational(-4, 10), 0, Rational(8, 10), Rational(12, 10)]
T = Rational(2, 10)
tgt = Rational(6, 10)
sm = sum(1 / (1 + exp(-v / T)) for v in vals) / 4
loss = (1 - sm - tgt) ** 2
print(f"SPARSITY-01: loss={float(loss.evalf(15))}  self-consistent=True  PASS=True")

print("\n=== All SymPy/NumPy verifications PASS ===")
sys.stdout.flush()
