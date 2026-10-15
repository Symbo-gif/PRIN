"""Z3 check: the driver's PNG colour-type rule equals the PNG specification.

The driver (``benchmarks/campaign/exp002_driver.py::_validate_png``) rejects a
PNG when a single Boolean expression over the IHDR colour type/bit depth and
the PLTE/tRNS placement and lengths holds. That expression is transcribed
below verbatim in Z3 form (``driver_rejects``), together with the per-chunk
PLTE length rule enforced earlier in the chunk loop. Independently, the PNG
specification's rules (W3C PNG 3rd ed., 11.2.1 IHDR table, 11.2.3 PLTE,
11.3.1.1 tRNS, 5.6 chunk ordering) are encoded as ``spec_valid``. Z3 then
searches the whole bounded domain for an input on which the two disagree.

Scope: colour/depth/PLTE/tRNS rules only — the IHDR field ranges, CRCs,
critical-chunk set and IDAT contiguity are checked elsewhere and are fixed as
valid here. ``unsat`` means no disagreement exists.
"""

from __future__ import annotations

import z3

colour, depth = z3.Ints("colour depth")
palette, transparency = z3.Bools("palette transparency")
palette_length, trns_length = z3.Ints("palette_length trns_length")
plte_index, trns_index, first_idat, trns_count = z3.Ints(
    "plte_index trns_index first_idat trns_count"
)

valid_depths = {0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 16)}


def depth_ok(c: z3.ArithRef, d: z3.ArithRef) -> z3.BoolRef:
    return z3.Or([z3.And(c == key, z3.Or([d == v for v in vals])) for key, vals in valid_depths.items()])


palette_entries = palette_length / 3  # integer division; only used when divisible

# --- driver, transcribed --------------------------------------------------
plte_loop_rejects = z3.And(
    palette,
    z3.Or(palette_length == 0, palette_length % 3 != 0, palette_length > 768),
)
pow2 = z3.If(depth == 1, 2, z3.If(depth == 2, 4, z3.If(depth == 4, 16, z3.If(depth == 8, 256, 65536))))
entries = z3.If(palette, palette_length / 3, 0)
trns_len = z3.If(transparency, trns_length, 0)
driver_rejects = z3.Or(
    plte_loop_rejects,
    z3.Not(depth_ok(colour, depth)),
    z3.And(colour == 3, z3.Not(palette)),
    z3.And(z3.Or(colour == 0, colour == 4), palette),
    z3.And(z3.Or(colour == 4, colour == 6), transparency),
    trns_count > 1,
    z3.And(palette, plte_index > first_idat),
    z3.And(transparency, trns_index > first_idat),
    z3.And(palette, transparency, trns_index < plte_index),
    z3.And(colour == 3, entries > pow2),
    z3.And(colour == 3, transparency, trns_len > entries),
    z3.And(colour == 0, transparency, trns_len != 2),
    z3.And(colour == 2, transparency, trns_len != 6),
)

# --- PNG specification, encoded independently ----------------------------
spec_palette_ok = z3.If(
    palette,
    z3.And(
        z3.Or(colour == 2, colour == 3, colour == 6),  # forbidden for 0 and 4
        palette_length % 3 == 0,
        palette_length >= 3,
        palette_length <= 3 * 256,
        z3.Implies(colour == 3, palette_length / 3 <= pow2),
        plte_index < first_idat,  # PLTE before the first IDAT
    ),
    colour != 3,  # PLTE is required for indexed colour
)
spec_trns_ok = z3.If(
    transparency,
    z3.And(
        trns_count == 1,
        z3.Or(colour == 0, colour == 2, colour == 3),  # forbidden with alpha
        trns_index < first_idat,
        z3.Implies(palette, trns_index > plte_index),
        z3.Implies(colour == 0, trns_length == 2),
        z3.Implies(colour == 2, trns_length == 6),
        z3.Implies(colour == 3, trns_length <= palette_length / 3),
    ),
    True,
)
spec_valid = z3.And(depth_ok(colour, depth), spec_palette_ok, spec_trns_ok)

domain = z3.And(
    colour >= 0, colour <= 10, depth >= 0, depth <= 32,
    palette_length >= 0, palette_length <= 2000,
    trns_length >= 0, trns_length <= 2000,
    plte_index >= 1, trns_index >= 1, first_idat >= 1,
    plte_index != first_idat, trns_index != first_idat,
    z3.Implies(z3.And(palette, transparency), plte_index != trns_index),
    trns_count >= 0, trns_count <= 3,
    transparency == (trns_count >= 1),
)

solver = z3.Solver()
solver.add(domain, driver_rejects == spec_valid)  # i.e. they disagree
result = solver.check()
print(f"z3 {z3.get_version_string()}: driver_rejects == spec_valid is {result}")
if result == z3.sat:
    print("counterexample:", solver.model())
    raise SystemExit(1)
print("RESULT: the driver's PNG colour rule equals the specification on the domain")

# Non-vacuity: dropping one driver term (PLTE after the first IDAT, the PR #33
# finding PR33-F8) must make the two disagree, so the check can fail.
weakened = z3.Or(
    [term for term in driver_rejects.children() if "plte_index > first_idat" not in str(term)]
)
probe = z3.Solver()
probe.add(domain, weakened == spec_valid)
assert probe.check() == z3.sat, "the equivalence check is vacuous"
print("non-vacuity: removing the PLTE-before-IDAT term yields a counterexample:", probe.model())
