-- EMA-007: Lean 4.34.0 re-elaboration of GRA-01-LEAN
-- (from prin-dynamics-graph-topology.json)
-- build_ring(N=6, k_ring=4) is 4-regular, no self-loops, 12 edges, connected.

def ringNbrs (i : Fin 6) : List (Fin 6) :=
  [i + 1, i - 1, i + 2, i - 2]

def dedup' [DecidableEq α] : List α → List α
  | [] => []
  | x :: xs => let rest := dedup' xs
               if rest.contains x then rest else x :: rest

def noDup [DecidableEq α] : List α → Bool
  | [] => true
  | x :: xs => !xs.contains x && noDup xs

example : ∀ i : Fin 6, (ringNbrs i).length = 4 := by decide
example : ∀ i : Fin 6, noDup (ringNbrs i) = true := by decide

example : ∀ i : Fin 6, !(ringNbrs i).contains i := by decide

def canon (p : Fin 6 × Fin 6) : Fin 6 × Fin 6 :=
  if p.1.val ≤ p.2.val then p else (p.2, p.1)

def allNodes : List (Fin 6) := [0, 1, 2, 3, 4, 5]

def allDirectedEdges : List (Fin 6 × Fin 6) :=
  allNodes.flatMap (fun i => (ringNbrs i).map (fun j => (i, j)))

def canonEdges : List (Fin 6 × Fin 6) :=
  dedup' (allDirectedEdges.map canon)

example : canonEdges.length = 12 := by decide

def stepClosure (visited : List (Fin 6)) : List (Fin 6) :=
  dedup' (visited ++ visited.flatMap ringNbrs)

def closureN : Nat → List (Fin 6) → List (Fin 6)
  | 0, v => v
  | n + 1, v => closureN n (stepClosure v)

example : allNodes.all (fun j => (closureN 6 [0]).contains j) = true := by decide

#eval "GRA-01 lean claim: 4-regular, no self-loops, 12 edges, connected -- all decided"
