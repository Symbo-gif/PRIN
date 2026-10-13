# EXP-002 — API, benchmark-result, and reproduction parity (track C1)

**Status:** E4 ANALYSED (session 0162, 2026-10-13 UTC) — H1 CONFIRMED, H2 CONFIRMED, **H3 REFUTED** (approved and §11.3 sensitivity policies), H4 CONFIRMED; **D1 flag RAISED** (campaign plan §10.4). E5 (session 0163) is READY: it reports in full and then blocks its successor. The protocol is FROZEN since the first `RUN-` (2026-10-12T21:27:05Z). (E3 executed at source `fae24c4` in session 0161; approved at E2, session 0160, 2026-10-12 UTC.)
**Campaign plan row:** [`DOCS/experiments/campaign-plan.md`](../campaign-plan.md) §2.1 (EXP-002).
**Raw artefact root:** [`benchmarks/results/EXP-002/`](../../../benchmarks/results/EXP-002/README.md)

## Current artefacts

| File | Created by | Frozen when |
|---|---|---|
| `preregistration.md` | E1, lead-authored ([`preregistration.md`](preregistration.md)) | E3 start (first `RUN-` directory created) — **frozen 2026-10-12T21:27:05Z**; SHA-256 `0f3073dd2ed73b64071bcf3ae182510a69a26bd575b81b5a97cc5a1f9bbc8c8b` |
| `e1-handoff.md` | E1 ([`e1-handoff.md`](e1-handoff.md)) | living handoff skeleton until E1 close |
| `e2-review-packet.md` | E1, lead-authored ([`e2-review-packet.md`](e2-review-packet.md)) | historical decision packet; superseded by `e2-review.md` |
| `e2-review.md` | E2 ([`e2-review.md`](e2-review.md)) | decisions, reasons, E3 entry checklist; frozen with the protocol at E3 start |
| `log.md` | E3 ([`log.md`](log.md)) | **written and closed at E3**; append-only, never edited after E3 close; aborted runs stay (none occurred). One erratum at E4: the freeze SHA quoted on line 1 (campaign plan §12.4; commit `7d850ba`) |
| `analysis/exp002_e4_analysis.py` | E4 ([`analysis/`](analysis/README.md)) | committed and pushed (`3731fc2`) before its first real run; unchanged afterwards |
| `analysis.md` | E4 ([`analysis.md`](analysis.md)) | the E4 record: pre-flight, gate, verdicts, D1, deviations, threats |
| `benchmarks/results/EXP-002/RUN-*` (five run directories) | E3 ([raw root](../../../benchmarks/results/EXP-002/README.md)) | immutable from creation; each closed by its own `manifest.json` |
| `EVIDENCE/0161/` | E3 ([`README.md`](../../../EVIDENCE/0161/README.md)) | byte-exact evidence: launch records, independent validation transcripts and tools, local gate, hosted results, cold reviews |
| `report.md` | E5 | after E5 approval; corrections are errata |
| `report-manifest.json` | E4 ([`report-manifest.json`](report-manifest.json)) | raw size and SHA-256 of the 7 analysis outputs and, separately, the 39 PRIN-arm publication files; input index of every run manifest, `R`, `F` and the input manifest (campaign plan §7.4) |
| `EVIDENCE/0162/` | E4 ([`README.md`](../../../EVIDENCE/0162/README.md)) | pre-flight, gates, cold reviews, run logs, DV-040 re-audit, hosted results |

The lead-authored collection driver is
[`benchmarks/campaign/exp002_driver.py`](../../../benchmarks/campaign/exp002_driver.py);
its synthetic regression tests are
[`tests/test_exp002_driver.py`](../../../tests/test_exp002_driver.py). The
driver admits only the APPROVED, committed protocol on a clean checkout;
E3 runs only under the e2-review.md §8 entry checklist. The PR #33 review
round amended the DRAFT and the driver before E2 (protocol section 11;
[`PR033-multi-review-audit.md`](../../audits/PR033-multi-review-audit.md)).

## Sessions

| Session | Stage | Brief | Status |
|---|---|---|---|
| 0159 | E1 — Pre-registration | [`0159-exp002-e1-api-benchmark-result-and-reproduction-parity.md`](../../sessions/phase-7/0159-exp002-e1-api-benchmark-result-and-reproduction-parity.md) | COMPLETE |
| 0160 | E2 — Review and approval | [`0160-exp002-e2-api-benchmark-result-and-reproduction-parity.md`](../../sessions/phase-7/0160-exp002-e2-api-benchmark-result-and-reproduction-parity.md) | COMPLETE |
| 0161 | E3 — Execution | [`0161-exp002-e3-api-benchmark-result-and-reproduction-parity.md`](../../sessions/phase-7/0161-exp002-e3-api-benchmark-result-and-reproduction-parity.md) | COMPLETE |
| 0162 | E4 — Analysis | [`0162-exp002-e4-api-benchmark-result-and-reproduction-parity.md`](../../sessions/phase-7/0162-exp002-e4-api-benchmark-result-and-reproduction-parity.md) | COMPLETE |
| 0163 | E5 — Report | [`0163-exp002-e5-api-benchmark-result-and-reproduction-parity.md`](../../sessions/phase-7/0163-exp002-e5-api-benchmark-result-and-reproduction-parity.md) | READY |

## Rules inherited from the campaign plan

- Hypotheses, expected results, and failure/abort conditions are committed
  **before** execution (Experimentation Standards §1.1–§1.2).
- Pre-register against the **reconciled** targets in campaign plan §2.1 and
  cite the reconciliation; hardware only from §5; seeds per §6
  (`seed_key = 2`); artefact layout per §7; budget cap per §8;
  statistics per §9; abort/D1 rules per §10.
- Raw artefacts are written only to new `RUN-<UTC>-<SHA>-<label>/` directories
  under the raw artefact root and closed with a per-run `manifest.json`.

## E3 to E4 handoff (session 0161, 2026-10-12 UTC)

**No hypothesis verdict was computed at E3.** The five records were validated for structure and
identity only (metadata, result envelope, declared artefact mapping, manifest, source / protocol /
input identity, seed pair `(0, 2)`, directory inventory). Their observation payloads (API rows,
claim cases, publication file records) were not examined (no value was compared, printed or interpreted;
`log.md` §10 states exactly what the tools parsed), no arm was compared with another, and no
analysis code was written. H1–H4 verdicts, the H3 report under both comparison policies (protocol
§11.3 item 1), every D1 determination and the exploratory analyses belong to E4 (session 0162).

**What E3 delivered.** Source `R` = `fae24c4393c7a0232e6c8f0a6388b1775aa5fc05`; protocol commit `F` =
`9a9889d08dcaf2ad0ce31659ed67721b54b114d0` (SHA-256 `0f3073dd2ed73b64071bcf3ae182510a69a26bd575b81b5a97cc5a1f9bbc8c8b`,
frozen at the first `RUN-` on 2026-10-12T21:27:05Z); operator MichaelMaillet; seed pair `(0, 2)` on every
run. Every leg ran once, in registered order, exit 0, `COMPLETED`, no abort-criterion trip, no D1
condition, no rerun. Aggregate CPU wall over all attempts 63.821 s against the 12 h cap. Tracked
bytes of the five records 339,128 B (largest run 97,963 B). Full detail, UTC times, digests and the
per-record validation transcripts are in [`log.md`](log.md) and `EVIDENCE/0161/`.

| # | Mode / label | Run directory under `benchmarks/results/EXP-002/` | Result file | Publication listing digest (e2-review.md §8 command, as measured) |
|---|---|---|---|---|
| 1 | `api` / `api-cpu` | `RUN-20261012T212705Z-fae24c4-api-cpu` | `api.json` | — |
| 2 | `conclusions` / `conclusions-cpu` | `RUN-20261012T213054Z-fae24c4-conclusions-cpu` | `conclusions.json` | — |
| 3 | `reference` / `reproduction-reference-cpu` | `RUN-20261012T213821Z-fae24c4-reproduction-reference-cpu` | `reproduction.json` | `d674de7d4b5830c9abf525fcc484a5ebc01e3620ca38b63badd037e289487323` |
| 4 | `prin` / `reproduction-prin-cpu` | `RUN-20261012T213936Z-fae24c4-reproduction-prin-cpu` | `reproduction.json` | `c1ca4ada167c50a28db2dfe4365d004cdb3621903f43e38cc6de75c2e4904669` |
| 5 | `repeatability` / `seedrep0-prin-cpu` | `RUN-20261012T214040Z-fae24c4-seedrep0-prin-cpu` | `reproduction.json` | `c1ca4ada167c50a28db2dfe4365d004cdb3621903f43e38cc6de75c2e4904669` |

**Retained, untracked artefacts.** `DOCS/test_and_benchmark_results/EXP-002/<run-id>/` (`inputs/` snapshot
and, for runs 3–5, `publication/`) is kept unmodified, outside git, until the E5 report is accepted
(E2 decision 8). E5 first verifies those bytes against the raw digests in each manifested
`reproduction.json`, then performs the protocol §8.2 reconstruction (protocol §11.3 item 2).

**For E4 (protocol §8).** Commit `analysis/exp002_e4_analysis.py` (a globally unique module basename
under this record root) **before** analysis starts; DV-040 option (a) gates (source-only Ruff format,
Ruff lint, strict mypy, non-vacuous Bandit over `DOCS/experiments/`) and Snyk Code apply. Accept exactly
the five run records and their manifests, verify provenance and input-byte identity before reading, and
re-derive the §4.1 decisions from retained operands, names and digests without trusting any
driver-provided success label. Report H3 under both the approved policy and the §11.3 sensitivity policy,
side by side. Preserve any negative result, and flag a D1 under campaign plan §10.4 if one occurs.

**Disclosures E4 and E5 must carry** (none is a registered abort criterion; each is recorded in
[`log.md`](log.md)):

1. `R` differs from the approval commit `9a9889d` by the single docs/evidence commit `fae24c4`; its only
   Python change adds four evidence file names to a manifest-completeness test (`tests/test_0160_manifest.py`).
   The e2-review.md §6 nightly disposition was applied on that basis.
2. The installed extension `python/prin/_prin_core.pyd` (SHA-256 `64ea1a2cf38cdbe43fc029c55e791e244b771b2909360c3890ae6f9224b47349`,
   written 2026-09-28T23:01:06Z) predates the latest Rust-source commits at `R` (DV-043 `e4f5b4e`, the DV-042
   doc attributes in `199b82a`, and the `cross_band_coupling_cpu` argument validation in `9a9889d`). It was not
   rebuilt, as in sessions 0159–0160, and the driver does not record it. EXP-002 exercises no Rust numerics.
3. The host was not otherwise idle in the editor-service sense (idle IDE, language-server and agent processes
   were present); no test, build, scan or agent task ran during any leg. EXP-002 measures no timing.
4. The pre-E2 outcome exposure (protocol §11.2) and its disposition (e2-review.md decision 9) stand unchanged.
   E3 did not examine any observation payload.
5. The first revision of the E3 per-record validator crashed, instead of failing a check, on a corrupted
   result file; it was fixed (revision 2, `log.md` §4.2). A read-only cold review then found the validator
   less strict than the driver's closure in several details, and revision 3 closed them: every record was
   re-validated (81, 80, 87, 87 and 87 checks, 0 failed) and each mode's mutation self-test passes
   (`log.md` §10). No admissibility outcome changed, and no driver gap that the review also found
   (junction ancestors, last-wins JSON, subset key checks) occurs in these records.
6. Not an experiment matter, but open: the hosted `rust` run on the E3 commit is red in one job, `audit`,
   because five new RustSec advisories (`quinn-proto 0.11.16`, an inactive optional dependency that is in
   no resolved dependency graph) entered the advisory database after the previous green run. `Cargo.lock`
   is unchanged and E3 touched no dependency; it was not remediated here and awaits the maintainer's
   decision (`log.md` §9).

## E4 to E5 handoff (session 0162, 2026-10-13 UTC)

**Verdicts** (pre-registration §4.1; exact counts; CIs and effect sizes not applicable):

| Hypothesis | Verdict | Observed |
|---|---|---|
| H1 | **CONFIRMED** | 175/175 api_symbols resolved; 172/172 legacy_api_names owned; 0 duplicate, removed or unexpected names; frozen-contract sets empty |
| H2 | **CONFIRMED** | 62/62 claim_comparator_records agree (C01 5/5, C02 42/42, C03 4/4, C04 5/5, C05 6/6) |
| H3, approved policy (primary) | **REFUTED** | 21/39 generated_files equal; 18 differ (PDF and PNG of figures 5, 7, 8, 9, 10, 11, 12, 14, 15); 0 missing, 0 extra; tables 11/11 equal and equal to the archived tables |
| H3, §11.3 sensitivity policy | **REFUTED** | 5/39 generated_files equal; 34 differ — the two policies agree, so H3 does not depend on the post-exposure amendment |
| H4 | **CONFIRMED** | 39/39 generated_files raw-identical between the two PRIN processes; canonical projection equal |

**D1 flag: RAISED** on H3, a publication-fidelity mismatch (pre-registration §4.3; campaign plan §10.4).
No cause is asserted at E4. E5 still completes and reports it in full, then blocks its successor; the
four contingency correction sessions and a new `EXP-002-r1` record follow. No correction session was
started, and no tolerance, policy or artefact changed.

**Analysis code:** `analysis/exp002_e4_analysis.py` at **`3731fc2`** (SHA-256 `7a400aa6…6ee4e4`),
committed and pushed before the first real run. Two runs produced byte-identical outputs.
**`report-manifest.json`** SHA-256 `6b15dcc112513cdce9cb2d923208f93d3616898225efed545706c56526e68781`.
All five records were admissible and none was aborted. Full record: [`analysis.md`](analysis.md).

**E5 must first** verify the retained publication bytes under
`DOCS/test_and_benchmark_results/EXP-002/<run-id>/publication/` against the raw digests manifested in each
`reproduction.json` (pre-registration §11.3 item 2), and **only then** reconstruct from a clean checkout of
the recorded source (§8.2). A reconstruction difference with verified retained bytes is a reconstruction
limitation, never a new H3/H4 observation. E5 regenerates the seven analysis outputs with the module at
`3731fc2` and matches `report-manifest.json`. The disclosures in `analysis.md` (stale extension, `R`
versus `F`, the pre-E2 exposure, the loaded host and the red Phase-A full-suite leg, `cargo audit`) carry
forward. Effect sizes and confidence intervals are not applicable (protocol §7), whatever the generic
wording of the 0163 brief. In the generated outputs, "tables equal to archived" counts the PRIN arm.
