-- EMA-007: Lean 4.34.0 re-elaboration of TEN-01-LEAN
-- (from prin-dynamics-tensor-contracts.json)
-- build_ring(N=6, k_ring=4, K=1.0)'s weighted coupling matrix is symmetric.

def WScaledRows : List (List Nat) :=
  [[0, 1, 1, 0, 1, 1],
   [1, 0, 1, 1, 0, 1],
   [1, 1, 0, 1, 1, 0],
   [0, 1, 1, 0, 1, 1],
   [1, 0, 1, 1, 0, 1],
   [1, 1, 0, 1, 1, 0]]

def WScaled (i j : Fin 6) : Nat :=
  ((WScaledRows.getD i.val []).getD j.val 0)

example : ∀ i j : Fin 6, WScaled i j = WScaled j i := by decide

#eval "TEN-01 lean claim: weight matrix symmetry -- decided"
