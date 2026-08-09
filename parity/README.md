# parity/ — golden-trajectory corpus and differential tests

Numerical parity against PRINet 3.0 is the highest-risk area of this rebuild
(project plan §7). This directory holds:

- `corpus/` — the golden-trajectory corpus generated **from the archived
  PRINet 3.0.0 source before any new code**: for every dynamics primitive
  (oscillator model × coupling mode × integrator), seeded float64 inputs and
  outputs — initial state, parameters, per-step trajectories (first 20 steps),
  and final metrics. Versioned JSON/NPZ; target ~500 golden cases.
- `test_parity_*.py` — differential pytest suite installing both the archived
  `prinet` 3.0.0 and the new build in one venv and asserting equivalence on
  the corpus plus hypothesis-generated random cases. Run in CI by
  `.github/workflows/parity.yml`.

## Tolerance policy

| Quantity | Tolerance |
|---|---|
| Trajectories (float64 reference) | `rtol=1e-6`, `atol=1e-8` |
| Chaotic regimes | statistical comparison (order-parameter time series) beyond the shadowing horizon, not pointwise |
| Metrics / decompositions (float64) | `rtol=2e-6`, `atol=1e-12` (amendments #16, #17: cross-platform torch regeneration noise up to ~1.1e-6 relative; single-runtime verification targets `rtol=1e-10`) |

## Public API

The Python implementation of the differential harness lives in `prin.parity`
(`python/prin/parity/`). Import it for manifest/loader access, case comparison,
and Hypothesis-driven fuzzing.

## Corpus summary

| Attribute | Value |
|---|---|
| Cases | 504 |
| Models | kuramoto (216), hopf (216), stuart_landau (72) |
| Couplings | full (216), mean_field (144), sparse_knn (144) |
| Integrators | euler (252), rk4 (252) |
| Steps stored | 20 |
| Array format | `.npz` with JSON manifest and per-file SHA-256 |

## Corpus generation

The reference implementation is installed from the archived source tree, not
from PyPI. With `prin[dev]` installed, run:

```bash
pip install -e "DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main"
python parity/generate_corpus.py --out parity/corpus/  # Phase 0 deliverable
```
