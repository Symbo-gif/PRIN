# paper/

Publication artefacts for the phase-resonance binding paper, carried over
unchanged from PRINet 3.0 (project plan §14) and wired to PRIN's reproduction
pipeline at WP-037 (session `0145`).

> **Provenance.** The `.tex` sources describe and quote the **PRINet 3.0
> reference implementation's** results. They are carried over verbatim — no
> number in them has been re-measured by PRIN. PRIN's own confirmatory
> measurements are a pre-registered Phase 7 campaign activity, and revising the
> paper's claims is explicitly out of scope for WP-037 ("Non-goals: Publishing
> 1.0 or replacing Phase 7 pre-registration"). Read every figure and table here
> as a historical reference result until the Phase 7 campaign report says
> otherwise.

## Contents

| Path | Tracked? | Description |
|---|---|---|
| `main.tex` | yes | Main paper source — 841 lines, 8 numbered sections plus an unnumbered Reproducibility Statement |
| `supplementary.tex` | yes | Supplementary material |
| `artefact_manifest.json` | yes | Governed SHA-256 manifest for the 172 stored benchmark JSON artefacts |
| `README.md` | yes | This file |
| `figures/README.md` | yes | Per-figure description table |
| `tables/README.md` | yes | Per-table description table |
| `figures/*.pdf`, `figures/*.png` | **no** — gitignored | 14 figures × 2 formats, regenerated |
| `tables/tab_*.tex` | **no** — gitignored | 11 LaTeX table fragments, regenerated |

`neurips_2026.sty` is deliberately **not** carried over: `main.tex` is
venue-neutral (`\documentclass[11pt]{article}` with a comment to that effect)
and neither source file loads the style, so it was an orphan in the reference
tree. Neither are the reference's compiled `main.pdf` / `supplementary.pdf` —
they are derived output.

## Regenerating the artefacts

Figures and tables are generated, never hand-edited. From the repository root:

```bash
# verify the manifest, then regenerate everything into paper/
python tools/reproduce.py --output-dir paper --verify-manifest

# or one class at a time
python tools/reproduce.py --figures-only --output-dir paper --verify-manifest
python tools/reproduce.py --tables-only  --output-dir paper --verify-manifest
```

A full run writes 39 files: 14 figures × (PDF + PNG) plus 11 tables. It needs
no training, no GPU, and no random sampling — it renders stored benchmark
values only. Rendering is deterministic (fixed 2000-01-01 PDF date, the `Agg`
backend, and `_FIXED_DATE` in `prin.reporting.figure_generation`), so a
regenerated artefact is byte-comparable to the one the manifest was built from.

The default output roots are `paper/figures` and `paper/tables`
(`prin.reporting.{figure,table}_generation.DEFAULT_OUTPUT_DIR`).
`tools/reproduce.py` reads its stored input JSON from the archived reference
tree and defaults to writing under `DOCS/test_and_benchmark_results/reproduction/`,
which is why the `--output-dir paper` flag is needed to populate this tree.

## Compiling

Regenerate the artefacts first — a fresh clone has no `figures/` or `tables/`
content, only their READMEs.

```bash
cd paper/
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex          # second pass for references
pdflatex -interaction=nonstopmode supplementary.tex
pdflatex -interaction=nonstopmode supplementary.tex
```

Requires a LaTeX distribution with the standard packages both sources load
(`fontenc`, `lmodern`, `geometry`, `microtype`, `amsmath`/`amssymb`/`amsfonts`/
`amsthm`, `booktabs`, `graphicx`, `hyperref`, `url`, `natbib`, `xcolor`,
`algorithm`, `algorithmic`, `multirow`, `caption`, `subcaption`, `wrapfig`,
`xspace`, `enumitem`). No LaTeX build runs in CI; compilation is a manual,
pre-submission step.

## Artefact wiring

Every artefact the sources reference is produced by the generators:

| Source | `\includegraphics` | `\input` |
|---|---|---|
| `main.tex` | `fig2_clevr_n_capacity`, `fig7_ablation_results`, `fig3_chimera_metrics`, `fig4_chimera_k_alpha_heatmap`, `fig6_oscillosim_scaling` | `tab_statistical`, `tab_stress`, `tab_ablation`, `tab_efficiency`, `tab_chimera`, `tab_oscillosim`, `tab_binding_params` |
| `supplementary.tex` | `fig8_parameter_efficiency`, `fig9_training_curves`, `fig10_statistical_summary`, `fig14_gradient_flow`, `fig13_representation_geometry` | `tab_param_efficiency`, `tab_occlusion` |

`\input` paths carry no `.tex` suffix; `\includegraphics` paths carry an
explicit `.pdf`. Both are relative to `paper/` — there is no `\graphicspath`.
`tests/test_paper_wiring.py` asserts this table stays true: it parses both
sources and checks every reference against the keys of
`prin.reporting.figure_generation.FIGURE_GENERATORS` and
`table_generation.TABLE_GENERATORS`.

Four figures and two tables are generated but referenced by neither source —
`fig5_mot_occlusion_comparison`, `fig11_flops_scaling`,
`fig12_supercritical_regime`, `fig15_noise_velocity`, `tab_geometry`,
`tab_supercritical`. They are kept because the generators are a faithful port
of the reference's full publication set and `tests/test_publication_generation.py`
asserts all 14 / all 11 by name; dropping them would weaken that contract.
There is no `fig1_*`: figure 1 never existed in the reference implementation.

## Artefact manifest

`artefact_manifest.json` is the governed SHA-256 manifest for the 172 immutable
stored benchmark JSON artefacts. Each record contains the plain filename, exact
byte size, and lowercase SHA-256 digest. The manifest is append-only: existing
records are verified before new ones are added, so mutation or removal of an
accepted artefact is a hard failure. `tools/reproduce.py --verify-manifest`
checks every stored artefact before rendering; `--append-manifest` adds new
artefacts only after all existing records verify.

## Known inconsistencies inherited from the reference

Carried over unchanged, so recorded rather than silently fixed:

1. `main.tex`'s `\author{}` block names one author (Michael Maillet); the
   reference `README.md`'s BibTeX named three. `CITATION.cff` at the repository
   root is PRIN's authoritative authorship record.
2. `\begin{thebibliography}{20}` declares a width of 20 but contains 15
   `\bibitem`s; `supplementary.tex` declares `{12}` and contains 10. The width
   argument only affects label spacing.
3. Two bibitems have author-label / key mismatches: `engelken2025horn` is
   labelled "Effenberger et al." and `ssa2025` is labelled "Hays(2026)".
4. The reference `README.md`'s "Paper Structure" list did not match the actual
   `\section` titles. The real structure is: Introduction, Background,
   `\prinet` Architecture, Experiments (6 subsections), Theoretical Analysis
   (2), Analysis, Discussion, Conclusion, and an unnumbered Reproducibility
   Statement.

Any of these may be corrected when the paper is revised against PRIN's own
Phase 7 campaign results; none is a reproduction-pipeline defect.

## License

MIT — see [LICENSE](../LICENSE).
