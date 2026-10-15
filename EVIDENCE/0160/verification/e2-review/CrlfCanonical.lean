/-
EXP-002 E2 decision 7 (table comparison), formal check in Lean 4 (core only).

`canon` models the driver's table canonicalization, Python's
`payload.replace(b"\r\n", b"\n")`: a left-to-right, non-overlapping scan that
emits LF for each CR LF pair and copies every other byte (13 = CR, 10 = LF).

`translate` models CPython's text-mode write on Windows (`newline=None`),
which the pinned reference `_save_table` uses: every LF is written as CR LF.

* `canon_translate`: `canon (translate x) = x` for every byte string `x`, so
  canonicalizing the reference arm's raw bytes recovers exactly the content
  string the reference generator wrote.
* `canon_noCRLF`: on a string with no CR immediately before an LF (the PRIN
  arm writes `newline="\n"`; the archived tables are LF), `canon` is the
  identity.

Together: equality of canonical table bytes means the two generators wrote the
same content, up to a CR immediately before an LF, and nothing weaker.
-/

def canon : List Nat → List Nat
  | [] => []
  | [h] => [h]
  | h :: b :: r => if h = 13 ∧ b = 10 then 10 :: canon r else h :: canon (b :: r)

def translate : List Nat → List Nat
  | [] => []
  | h :: t => if h = 10 then 13 :: 10 :: translate t else h :: translate t

theorem translate_head (t : List Nat) (b : Nat) (r : List Nat)
    (ht : translate t = b :: r) : b ≠ 10 := by
  cases t with
  | nil => simp [translate] at ht
  | cons a s =>
    by_cases ha : a = 10
    · simp [translate, ha] at ht
      omega
    · simp [translate, ha] at ht
      omega

theorem canon_translate : ∀ x : List Nat, canon (translate x) = x
  | [] => by simp [translate, canon]
  | h :: t => by
    by_cases hh : h = 10
    · subst hh
      simp [translate, canon, canon_translate t]
    · have ih := canon_translate t
      simp only [translate, hh, ite_false]
      cases ht : translate t with
      | nil =>
        rw [ht] at ih
        simp [canon] at ih
        simp [canon, ← ih]
      | cons b r =>
        have hb := translate_head t b r ht
        rw [ht] at ih
        simp [canon, hb, ih]

def NoCRLF : List Nat → Prop
  | [] => True
  | [_] => True
  | h :: b :: r => ¬(h = 13 ∧ b = 10) ∧ NoCRLF (b :: r)

theorem canon_noCRLF : ∀ x : List Nat, NoCRLF x → canon x = x
  | [] => fun _ => by simp [canon]
  | [_] => fun _ => by simp [canon]
  | h :: b :: r => fun hx => by
    simp only [NoCRLF] at hx
    obtain ⟨hpair, hrest⟩ := hx
    have ih := canon_noCRLF (b :: r) hrest
    simp [canon, hpair, ih]
