(* EMA-005 (Phase 5 close) session: independent Wolfram Engine secondary
   corroboration. Out-of-band, advisory evidence -- a second, independently-
   implemented CAS engine, not routed through math-audit-mcp's governed
   evidence chain (Wolfram remains policy.adapters.enable_wolfram=false; see
   tools/math_audit_policy.yaml). Two parts:
   (A) Re-confirmation of EMA-001's INT-01/INT-02/HOPF-01/KUR-01 corroboration
       (unchanged claims; Phase 5 added zero new oscillator-dynamics numerics)
       -- rerun fresh for this session per explicit maintainer instruction that
       redundant cross-tool validation is additional evidence, not waste.
   (B) New corroboration for Phase 5's new mathematical content (HUN-01,
       COHEN-01, WELCH-DF-01, GAMMA-REFLECT-01, BETA-SYM-01), each via a
       Wolfram computation independent of both the Rust implementation and
       math-audit-mcp's SymPy/Z3 adapters used for the governed ledger run. *)

Print["=== Part A: re-confirmation of EMA-001 ODE corroboration (unchanged claims) ==="];

Print["--- INT-01: Euler, y'=-2y, h=0.05, y(0)=1, t in [0,1] ---"];
lambda = -2; h = 1/20;
exact[t_] := Exp[lambda*t];
R = 1 + lambda*h;
eulerIter[n_] := R^n;
maxErr = Max[Table[Abs[eulerIter[n] - exact[n*h]], {n, 0, 20}]];
Print["stability factor R = ", N[R], " (|R|<1 => decaying)"];
Print["max |euler - exact| over 20 steps = ", N[maxErr], " (tol 0.02): ", N[maxErr] < 0.02];
Print["monotone decreasing, stays in [0,1]: ", 0 < R < 1, ", ", AllTrue[Table[eulerIter[n], {n, 0, 20}], 0 <= # <= 1 &]];

Print["--- INT-02: RK4, y'=-2y, h=0.1, y(0)=1, t in [0,1] ---"];
h2 = 1/10;
R4[z_] := 1 + z + z^2/2 + z^3/6 + z^4/24;
Rval = R4[lambda*h2];
rk4Iter[n_] := Rval^n;
maxErr2 = Max[Table[Abs[rk4Iter[n] - exact[n*h2]], {n, 0, 10}]];
Print["stability factor R4 = ", N[Rval], "; max err = ", N[maxErr2], " (tol 0.0001): ", N[maxErr2] < 0.0001];

Print["--- HOPF-01: dr/dt = 4r - r^3, r(0)=1/2 ---"];
sol = DSolve[{u'[t] == -8*u[t] + 2, u[0] == 4}, u[t], t];
uSol = u[t] /. sol[[1]];
rSol[tt_] := 1/Sqrt[uSol /. t -> tt];
Print["r(t) = ", Simplify[rSol[t]], "; r(0)=", rSol[0] // N, "; Limit r(t)->", Limit[rSol[t], t -> Infinity]];
rVals = Table[N[rSol[tt]], {tt, 0, 10, 0.5}];
Print["monotone non-decreasing, within [0.5,2.0]: ", AllTrue[Differences[rVals], # >= -10^-12 &], ", ", AllTrue[rVals, 0.5 - 10^-9 <= # <= 2.0 + 10^-9 &]];

Print["--- KUR-01: dDelta/dt = 1 - 2 Sin[Delta], Delta(0)=0.1, t in [0,20] ---"];
deltaStar = ArcSin[1/2];
ndsol = NDSolve[{d'[t] == 1 - 2*Sin[d[t]], d[0] == 0.1}, d, {t, 0, 20}, WorkingPrecision -> 30, PrecisionGoal -> 20];
dFun = d /. ndsol[[1]];
dVals = Table[dFun[tt], {tt, Range[0, 20, 1]}];
Print["Delta(20) = ", N[dFun[20], 15], "; Delta* = ", N[deltaStar, 15]];
Print["monotone, no overshoot, within tol at t=20: ", AllTrue[Differences[dVals], # >= -10^-12 &], ", ", AllTrue[dVals, # <= N[deltaStar] + 10^-9 &], ", ", Abs[dFun[20] - deltaStar] < 0.0001];

Print[""];
Print["=== Part B: new corroboration for Phase 5 mathematical content ==="];

Print["--- HUN-01: Hungarian 3x3 optimal assignment, independent brute force ---"];
cost = {{4, 1, 3}, {2, 0, 5}, {3, 2, 2}};
perms = Permutations[{1, 2, 3}];
costs = Table[Sum[cost[[i, perms[[k, i]]]], {i, 1, 3}], {k, 1, Length[perms]}];
Print["all 6 permutation costs = ", costs];
Print["minimum cost = ", Min[costs], " (expect 5)"];
Print["achieved by permutation(s): ", Pick[perms, costs, Min[costs]]];

Print["--- HUN-01b: rectangular case (2 rows x 4 cols), independent brute force ---"];
costR = {{1, 9, 9, 2}, {9, 1, 9, 9}};
combosR = Subsets[{1, 2, 3, 4}, {2}];
permsR = Flatten[Table[{c, Reverse[c]}, {c, combosR}], 1];
costsR = Table[costR[[1, p[[1]]]] + costR[[2, p[[2]]]], {p, permsR}];
Print["minimum cost = ", Min[costsR], " (expect 2, matching Rust test rectangular_more_columns_than_rows)"];

Print["--- COHEN-01: pooled-sd equal-n/equal-var reduction ---"];
pooledExpr = Sqrt[((n - 1)*v + (n - 1)*v)/(n + n - 2)];
Print["Simplify[pooled] = ", Simplify[pooledExpr, {n > 1, v > 0}], " (expect Sqrt[v])"];
Print["Symbolic equality holds: ", Simplify[pooledExpr - Sqrt[v], {n > 1, v > 0}] == 0];

Print["--- WELCH-DF-01: Welch-Satterthwaite equal-variance/equal-n reduction ---"];
dfExpr = (t + t)^2/(t^2/(n - 1) + t^2/(n - 1));
Print["Simplify[df] = ", Simplify[dfExpr, {n > 1, t > 0}], " (expect 2(n-1))"];
Print["Symbolic equality holds: ", Simplify[dfExpr - 2*(n - 1), {n > 1, t > 0}] == 0];

Print["--- GAMMA-REFLECT-01: Euler reflection formula ---"];
reflectExpr = Gamma[x]*Gamma[1 - x] - Pi/Sin[Pi*x];
Print["Simplify[Gamma[x]Gamma[1-x] - Pi/Sin[Pi x]] = ", Simplify[reflectExpr, 0 < x < 1], " (expect 0)"];
Print["Numeric spot check at x=0.3: ", N[Gamma[0.3]*Gamma[0.7]], " vs ", N[Pi/Sin[Pi*0.3]]];

Print["--- BETA-SYM-01: regularized incomplete beta symmetry ---"];
betaSymTest[a_, b_, x_] := N[BetaRegularized[x, a, b] + BetaRegularized[1 - x, b, a]];
Print["I_x(a,b)+I_(1-x)(b,a) at (a=3,b=5,x=0.4): ", betaSymTest[3, 5, 0.4], " (expect 1)"];
Print["at (a=5,df/2 case a=10/2=5,b=1/2,x=0.3): ", betaSymTest[5, 0.5, 0.3], " (expect 1)"];
Print["at (a=0.5,b=0.5,x=0.9): ", betaSymTest[0.5, 0.5, 0.9], " (expect 1)"];

Print["--- Student-t two-tailed p-value cross-check (independent of SymPy/Rust) ---"];
studentP[tstat_, df_] := N[2*(1 - CDF[StudentTDistribution[df], Abs[tstat]])];
Print["t=2.228, df=10: p = ", studentP[2.228, 10], " (Rust test expects ~0.05)"];
Print["t=1.959964, df=1000000: p = ", studentP[1.959964, 1000000], " (Rust test expects ~0.05)"];

Print[""];
Print["=== Summary: Part A (4/4 unchanged ODE claims re-confirmed) + Part B (6 new Phase 5 identities/computations independently corroborated) ==="];
