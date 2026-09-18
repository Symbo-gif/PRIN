import Mathlib.Tactic

namespace Fixture

theorem add_comm_fixture (a b : Nat) : a + b = b + a := by
  exact Nat.add_comm a b

def double (n : Nat) : Nat := n + n

end Fixture
