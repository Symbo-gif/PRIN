# paper/tables/

LaTeX table fragments for the NeurIPS 2026 paper — 11 tables included via `\input{}` in `main.tex` and `supplementary.tex`.

## Tables

| File | Description |
|---|---|
| `tab_ablation.tex` | Ablation study results: attention-only, oscillators-only, hybrid |
| `tab_binding_params.tex` | Binding-specific parameter counts (PT 379 vs SA 54,336) |
| `tab_chimera.tex` | Chimera state statistics (BC, local order parameter distributions) |
| `tab_efficiency.tex` | Computational efficiency comparison (FLOPs, latency, memory) |
| `tab_geometry.tex` | Representation geometry metrics (k-NN purity, intrinsic dimensionality) |
| `tab_occlusion.tex` | Occlusion recovery sweep results across difficulty levels |
| `tab_oscillosim.tex` | OscilloSim benchmark results across oscillator counts and coupling modes |
| `tab_param_efficiency.tex` | Detailed parameter efficiency analysis (O(1) vs O(d²)) |
| `tab_statistical.tex` | Statistical tests: TOST equivalence, Bayesian, Cliff's delta, Holm-Bonferroni |
| `tab_stress.tex` | Stress test results: high object count, long sequences, extreme noise |
| `tab_supercritical.tex` | Supercritical regime analysis (K_eff/K_c ratios) |

## Regeneration

Every table here is derived output, not a source file. From the repository
root:

```bash
python tools/reproduce.py --tables-only --output-dir paper --verify-manifest
```

`main.tex` and `supplementary.tex` `\input` these by stem with no extension
(`\input{tables/tab_statistical}`). The generated `tab_*.tex` files are
gitignored — regenerate them rather than committing them. `prin.reporting.table_generation`
is byte-faithful to the reference tables: `tests/test_publication_generation.py`
diffs every regenerated `tab_*.tex` against the archived PRINet 3.0 file.

## License

MIT — see [LICENSE](../../LICENSE).
