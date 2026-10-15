# EXP-002 D1 correction — S1 evidence

Status: **current** (S1 complete, 2026-10-15 UTC). This directory holds the
pre-fix reproduction and decomposition at the failing-test commit `d90eeab`,
and the post-fix decomposition and green gate at `9371596`. The record of
this S1 is
[`DOCS/audits/2026-10-15-exp002-d1-correction-audit.md`](../../DOCS/audits/2026-10-15-exp002-d1-correction-audit.md).

Root-cause evidence for the EXP-002 D1 correction cycle, session S1
([brief](../../DOCS/sessions/contingencies/2026-10-14-exp002-d1-s1-correction-implementation.md)).
Every file here was generated on the E3 host (Windows 11, project venv,
Python 3.14.0, Matplotlib 3.11.1, NumPy 2.5.1, Agg renderer, the E3 font set
and font cache), run from the repository root.

| File | What it is |
|---|---|
| [`root_cause_decomposition.py`](root_cause_decomposition.py) | Generator. For each of the 14 registered figure stems it renders the frozen PRINet 3.0 function (**R**), PRIN's port (**P**), the reference with every registered divergence applied (**A**), and the reference with each divergence applied alone (**R_d**). It compares them under the registered H3 rule, `benchmarks.campaign.exp002_driver.normalized_bytes`. It also verifies the committed E3 run records and the retained E3 bytes, and checks PRIN's raw-byte determinism across two processes. |
| [`root-cause-decomposition-prefix.json`](root-cause-decomposition-prefix.json) | That run against the **pre-fix** port at `d90eeab` (`port_module_sha256` `e0f59253…d533`). |
| [`decomposition-prefix-run.txt`](decomposition-prefix-run.txt) | Verbatim console output and exit code of the prefix run. |
| [`gate-red-d90eeab.txt`](gate-red-d90eeab.txt) | Verbatim run of `parity/test_parity_publication.py` at the failing-test commit: **18 failed, 75 passed**. The 18 failures are exactly the E3 population (failure tracebacks trimmed; the summary is verbatim). |
| [`gitleaks-history-d90eeab.txt`](gitleaks-history-d90eeab.txt) | Pre-push full-history secret scan (Plan amendment #48 item 6): 731 commits, no leaks, exit 0. |
| [`root-cause-decomposition-postfix.json`](root-cause-decomposition-postfix.json) | The same run against the **post-fix** port at `9371596` (`port_module_sha256` `b41dfc13…c048`, identical to the fix commit `10d84f2`). 0 of 39 files differ from the reference. A, the reference with all 34 divergences applied, still equals the pre-fix port digests in the committed prefix artefact, and the divergence and materiality results equal the prefix run's. The 21 files that matched at E3 stay raw-identical to E3's PRIN arm, and exactly the 18 D1 files changed. Two separate PRIN processes agree on every raw byte (H4). |
| [`decomposition-postfix-run.txt`](decomposition-postfix-run.txt) | Verbatim console output and exit code of the postfix run. |
| [`gate-green-9371596.txt`](gate-green-9371596.txt) | Verbatim run of `parity/test_parity_publication.py` plus the nine fast-gate argument tests (`tests/test_publication_figure_arguments.py`) on the post-fix tree: **102 passed**, exit 0. |
| [`snyk-code.txt`](snyk-code.txt) | Snyk Code (`snyk code test . --severity-threshold=low`) summary and a SARIF filter: **0 findings** in the four new or modified first-party source files. The repository has 75 LOW findings in total, all in files this change does not touch, and 0 medium or high. |
| [`local-gate.txt`](local-gate.txt) | Verbatim local gate (Plan amendment #48): the commands, their exit codes, and the commit and host they ran on. |

## Method: controlled substitution on the frozen reference

A *divergence* is one concrete difference between a reference drawing call
and the pre-fix port. It can be a keyword argument the port dropped, a label
string it re-encoded from Unicode to mathtext, or a call it omitted. The
generator applies a divergence to the frozen reference **without editing or
re-executing its source**. While a stem renders, the named
`matplotlib.axes.Axes` method is wrapped, and only calls whose immediate
caller is `prinet.utils.figure_generation` are transformed. Matplotlib's
internal calls pass through untouched. Each transform asserts that the
argument it changes is present in the reference call, and each divergence
must fire at least once. A specification that does not match the reference
source therefore aborts the run.

## Result (pre-fix, `root-cause-decomposition-prefix.json`)

- **Reproduction.** In-process, the reference arm equals E3's reference arm
  on all 39 normalized digests. PRIN's tree equals E3's PRIN arm on all 39
  raw digests. The committed E3 records differ on exactly the 18-file D1 set.
  All three retained E3 publication roots (reference, PRIN, seed-replicate 0)
  match their manifested `reproduction.json` on 39/39 raw and 39/39
  normalized digests, and each `reproduction.json` matches its run
  `manifest.json`.
- **Completeness.** For every one of the nine D1 stems, **A == P** in both
  formats. The 34 registered divergences account for the entire byte
  difference. Nothing outside them differs: every plotted value, data
  series, axis limit, title and annotation number is identical. **Unexplained
  stems: 0.**
- **Materiality.** 26 of the 34 divergences change bytes when applied alone.
  The other 8 equal the active rcParam or have no visible effect, so a
  faithful port still mirrors them.
- **Side.** Every divergence is a drawing argument that the PRIN port
  (`d88a331`, WP-034 S1) changed relative to the frozen reference generator
  it ports. No divergence touches a computed quantity, so no reference
  calculation is implicated. The defective side is **PRIN**, and campaign
  plan §10.4 item 3 (a claim that the reference is defective) is **not
  invoked**.

| Stem | Byte-material divergences (reference → pre-fix port) | Immaterial | PNG pixels differing (P vs R) |
|---|---|---|---|
| `fig5_mot_occlusion_comparison` | D5.2 `errorbar` `markersize=4` dropped; D5.4 `plot` `markersize=4` dropped (both fall back to rc `lines.markersize=5`) | D5.1, D5.3 `linewidth=1.5` (= rc) | 4,765 |
| `fig7_ablation_results` | D7.1 accuracy-label `text` `va="bottom"` dropped | — | 2,284 |
| `fig8_parameter_efficiency` | D8.1 `scatter` `zorder=5` dropped (markers drawn under the grid) | — | 505 |
| `fig9_training_curves` | D9.1 four loss curves `linewidth=1.2` dropped; D9.3 IP-label `text` `va="bottom"` dropped | D9.2 legend `loc="upper right"` (`"best"` picks the same corner) | 12,936 |
| `fig10_statistical_summary` | D10.1 outcome `annotate` `bbox` (round, light-yellow) dropped | — | 26,705 |
| `fig11_flops_scaling` | D11.1/D11.2 `bar` `edgecolor="black"`/`linewidth=0.5` dropped; D11.3 y-label Unicode `×10³` → mathtext; D11.5 ratio labels Unicode `×` → mathtext; D11.6 ratio `annotate` `va="bottom"` dropped | D11.4 legend `framealpha=0.8` (= rc) | 58,922 |
| `fig12_supercritical_regime` | D12.1 `bar` `linewidth=0.5` dropped; D12.2 band tick labels Unicode (δ/θ/γ, en dash) → mathtext; D12.3/D12.4 `axhline` `linewidth=0.8`/`alpha=0.7` dropped; D12.6 twin `plot` `linewidth=1.2` dropped; D12.8 twin `tick_params(labelcolor=…)` omitted; D12.9 ratio labels Unicode `×` → mathtext; D12.10 ratio `text` `va="bottom"` dropped | D12.5 `markersize=5` (= rc); D12.7 line `label` (no legend) | 44,801 |
| `fig14_gradient_flow` | D14.1 `barh` `alpha=0.85` dropped | — | 49,834 |
| `fig15_noise_velocity` | D15.1 noise lines `markersize=3` dropped; D15.2/D15.3 fit line `alpha=0.5`/`linewidth=1` dropped; D15.5 velocity lines `markersize=4` dropped; D15.6 x-label Unicode `×` → mathtext | D15.4, D15.7 legend `loc="lower left"` (`"best"` picks the same corner) | 18,292 |

The five figures that matched at E3 (`fig2`, `fig3`, `fig4`, `fig6`,
`fig13`) carry no registered divergence, and their remaining source
differences change no byte. Examples are call order and `ax.set(...)`
grouping, and fig13's unused per-series `label=`.

**Why the port diverged.** The Unicode-to-mathtext re-encodings coincide with
`ruff`'s `RUF001` ambiguous-character rule, which this repository enables:
`×` reads as `x` and `γ` as `y`. The dropped keyword arguments read as
condensation during the port. No test compared figure bytes with the
reference, because `tests/test_publication_generation.py` asserts figure
completeness and normalization only. That is the gap the new gate closes.

## Result (post-fix, `root-cause-decomposition-postfix.json`)

All 39 publication files equal the reference under the registered H3
comparison (`port_vs_reference_differing_count: 0`, PNG pixels differing 0
on every stem). The 21 outputs that matched at E3 are raw-byte-identical to
E3's PRIN arm. Two separate PRIN processes still agree on every raw byte. A
still equals the pre-fix port digests recorded in the prefix artefact, and
every divergence's materiality is unchanged.

## Regenerating

From the repository root with the project venv (the retained E3 roots under
`DOCS/test_and_benchmark_results/EXP-002/` are read when present; the script
reports `retained_root_present: false` once they are removed):

```bash
python EVIDENCE/exp002-d1-s1/root_cause_decomposition.py --label postfix \
    --out EVIDENCE/exp002-d1-s1/root-cause-decomposition-postfix.json
```

A postfix run compares A against the pre-fix port digests in the committed
prefix artefact (`--prefix`, which defaults to the sibling
`root-cause-decomposition-prefix.json`). The label is derived from the
imported build: `prefix` if any stem differs from the reference, `postfix`
otherwise. A mismatched `--label` exits 2 and writes nothing. The port is
pure Python, so the prefix artefact can be regenerated after the fix with
`--label prefix --out …/root-cause-decomposition-prefix.json` by
temporarily restoring the pre-fix module:
`git restore --source d90eeab -- python/prin/reporting/figure_generation.py`.
Run the command above, then `git restore python/prin/reporting/figure_generation.py`.
The artefact's `port_module_sha256` identifies the module that was measured.
