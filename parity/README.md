# parity/ — golden-trajectory corpus and differential tests

Numerical parity against PRINet 3.0 is the highest-risk area of this rebuild
(project plan §7). This directory holds:

- `corpus/` — the golden-trajectory corpus generated **from PRINet 3.0.0 before
  any new code**: for every dynamics primitive (oscillator model × coupling
  mode × integrator), seeded float64 inputs and outputs — initial state,
  parameters, per-step trajectories (first 100 steps), and final metrics.
  Versioned JSON/NPZ; target ~500 golden cases.
- `test_parity_*.py` — differential pytest suite installing both
  `prinet==3.0.0` and the new build in one venv and asserting equivalence on
  the corpus plus hypothesis-generated random cases. Run in CI by
  `.github/workflows/parity.yml`.

## Tolerance policy

| Quantity | Tolerance |
|---|---|
| Trajectories (float64 reference) | `rtol=1e-6`, `atol=1e-8` |
| Chaotic regimes | statistical comparison (order-parameter time series) beyond the shadowing horizon, not pointwise |
| Metrics / decompositions (float64) | `rtol=1e-10` |

## Corpus generation

```bash
pip install "prinet==3.0.0"
python parity/generate_corpus.py --out parity/corpus/  # Phase 0 deliverable
```
