# prin.parity — golden-trajectory corpus and differential harness

Pure-Python package (no oscillator numerics) that supports the PRIN numerical
parity program. It provides the schema, manifest, loader, comparison harness,
and Hypothesis strategies used to assert that new Rust/Python code matches the
archived PRINet 3.0.0 reference within documented tolerances.

| Module | Contents |
|---|---|
| `schema.py` | `CaseSpec`, `CaseArrays`, `CorpusValidationError`, tolerances, and validation helpers. |
| `manifest.py` | `CorpusManifest`, `ManifestRecord`, SHA-256 validation, and manifest creation. |
| `loader.py` | `CorpusLoader` and `LoadedCase`; validates digests and array shapes on load. |
| `harness.py` | `compare_arrays`, `compare_case`, `assert_parity`, and planted-deviation helpers. |
| `strategies.py` | Hypothesis strategies for generating valid seeded parity cases. |

Tolerances are defined in `DOCS/standards/Testing_Standards.md` §3:

| Quantity | Tolerance |
|---|---|
| Trajectories (float64 reference) | `rtol=1e-6`, `atol=1e-8` |
| Metrics / decompositions (float64) | `rtol=2e-6`, `atol=1e-12` (amendments #16, #17: cross-platform torch regeneration noise; single-runtime verification targets `rtol=1e-10`) |

See `parity/README.md` for the on-disk corpus layout and the archive-based
reference install.
