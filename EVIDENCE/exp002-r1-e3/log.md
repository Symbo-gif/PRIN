# EXP-002-r1 E3 Operator Execution Log

**Session:** `EXP-002-r1 E3` (Experiment Execution and Raw Evidence Collection, track C1)  
**Project:** PRIN (`prin-core 1.0.0rc1` / Rust `1.0.0-rc1`)  
**Operator:** MichaelMaillet  
**AI Pair of Record:** Antigravity (E3 execution agent)  
**Execution Timestamp:** 2026-10-21 UTC  
**Governed Reference Host:** Windows 11 (AMD64 Family 25 Model 117 Stepping 2, AuthenticAMD)  
**Python Environment:** Python 3.14.0 (`.venv\Scripts\python.exe`)  
**PyTorch:** 2.11.0+cu128 (CUDA available: True, CPU execution mandated for reproducibility)  
**Clean Execution Head SHA ($R):** `e65076eb7ae97100d40ea32c60229dd40ed51033`  
**Short SHA ($R7):** `e65076e`  

---

## 1. Entry Verification and Pre-Flight Checks

1. **PR #37 Merge Verification:**
   - PR #37 merged into `main` at commit `e65076eb7ae97100d40ea32c60229dd40ed51033`.
   - Branch `campaign/exp002-r1-e3` created directly from `origin/main` at HEAD `e65076eb7ae97100d40ea32c60229dd40ed51033`.
   - Git working tree: clean (`git status --porcelain` returned 0 entries).

2. **Pre-Registration Status:**
   - File: `DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/preregistration.md`
   - Status: `**Status:** APPROVED`
   - Maintainer Approval: `**Maintainer approval:** MichaelMaillet, 2026-10-21 UTC`

3. **Governed Native Extension Pin Gate (DV-047 closure):**
   - File: `python/prin/_prin_core.pyd`
   - Size: `9,290,240` bytes (exact match)
   - SHA-256: `37392d067efa3983e384c94f4ac2268c4fad2f5ea929c529b3db50bff4fee99e` (exact match)

4. **Shadow File Audit:**
   - Untracked `*.py` / `*.pth` search across repo root, `python/`, `benchmarks/`, `tools/`: 0 files found.

5. **Predecessor Immutability Audit:**
   - Command: `git diff HEAD -- DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/ benchmarks/results/EXP-002/ DOCS/test_and_benchmark_results/EXP-002/ EVIDENCE/0159/ EVIDENCE/0160/ EVIDENCE/0161/ EVIDENCE/0162/ EVIDENCE/0163/ EVIDENCE/exp002-d1-s1/ EVIDENCE/exp002-d1-s2/ EVIDENCE/exp002-d1-s3/ EVIDENCE/exp002-d1-s4/`
   - Result: clean (0 bytes diff output, exit code 0).

---

## 2. Sequential Run Execution Sequence

The 5 registered runs were executed sequentially in separate interpreter processes in the exact order specified in `preregistration.md` §5.5:

### Run 1: API Census (H1)

- **Mode:** `api`
- **Run Directory:** `benchmarks/results/EXP-002-r1/RUN-20261021T183011Z-e65076e-r1-api-cpu`
- **Command Line:**
  ```powershell
  .venv\Scripts\python -m benchmarks.campaign.exp002_r1_driver --mode api --run-dir benchmarks/results/EXP-002-r1/RUN-20261021T183011Z-e65076e-r1-api-cpu --operator MichaelMaillet --source-sha e65076eb7ae97100d40ea32c60229dd40ed51033 --seed-counter 0 --seed-key 2
  ```
- **Execution Timestamp (UTC):** START `20261021T183011Z`
- **Exit Code:** `0`
- **Manifest Contents:**
  - `api.json` (97,334 bytes, SHA-256 `1dcd87ff4c258cb6a2e30dd8b96e0ce180729460702630107aea96c13912d7d3`)
  - `campaign-metadata.json` (230 bytes, SHA-256 `7137d320fab9955bdcbdd66477f7dadee6c8d484c04de1c4862f5a0390e46fa2`)
  - `manifest.json` (554 bytes, SHA-256 `b859dba6739cfc420f1d89ecb322d9b8e01f918151eaea827cfca00b6f6a723c`)
- **Validation:** `check_run_complete()` passed. 175 symbols introspected against 172 legacy symbols. No `abort.json`.

### Run 2: Archival Conclusions Census (H2)

- **Mode:** `conclusions`
- **Run Directory:** `benchmarks/results/EXP-002-r1/RUN-20261021T183952Z-e65076e-r1-conclusions-cpu`
- **Command Line:**
  ```powershell
  .venv\Scripts\python -m benchmarks.campaign.exp002_r1_driver --mode conclusions --run-dir benchmarks/results/EXP-002-r1/RUN-20261021T183952Z-e65076e-r1-conclusions-cpu --operator MichaelMaillet --source-sha e65076eb7ae97100d40ea32c60229dd40ed51033 --seed-counter 0 --seed-key 2
  ```
- **Execution Timestamp (UTC):** START `20261021T183952Z`
- **Exit Code:** `0`
- **Manifest Contents:**
  - `conclusions.json` (59,346 bytes, SHA-256 `f61f5575fb8d28646c583e15923236e2b22c32bcfc00a9acd25b4f73eacb2a87`)
  - `campaign-metadata.json` (254 bytes, SHA-256 `c2cd7800763a36bf01d0e29ea01f1d26d6451680d61c25a81f7019428303bb4f`)
  - `manifest.json` (562 bytes, SHA-256 `af3164f093eb4030ff98d9a905da452d6bf7193983d61d76fe65561ea6a6ec82`)
- **Validation:** `check_run_complete()` passed. 62 claim cases evaluated. No `abort.json`.

### Run 3: Reference Reproduction Arm (H3)

- **Mode:** `reference`
- **Run Directory:** `benchmarks/results/EXP-002-r1/RUN-20261021T184447Z-e65076e-r1-reproduction-reference-cpu`
- **Command Line:**
  ```powershell
  .venv\Scripts\python -m benchmarks.campaign.exp002_r1_driver --mode reference --run-dir benchmarks/results/EXP-002-r1/RUN-20261021T184447Z-e65076e-r1-reproduction-reference-cpu --operator MichaelMaillet --source-sha e65076eb7ae97100d40ea32c60229dd40ed51033 --seed-counter 0 --seed-key 2
  ```
- **Execution Timestamp (UTC):** START `20261021T184447Z`
- **Exit Code:** `0`
- **Manifest Contents:**
  - `reproduction.json` (59,724 bytes, SHA-256 `eaeddfb0ad06b49f0a1390207540f6303ed23e1a432807f95ae34aa6513f4493`)
  - `campaign-metadata.json` (264 bytes, SHA-256 `1cdd61267c68542a7b2ff0d3f2a08e8ee112a050256d03e547d077e9f867295e`)
  - `manifest.json` (563 bytes, SHA-256 `a8b88998535be9ab23dbcbf538de41e1f1704908ca9426f5704f66da3fafe8e7`)
- **Retained Outputs:** `DOCS/test_and_benchmark_results/EXP-002-r1/RUN-20261021T184447Z-e65076e-r1-reproduction-reference-cpu/` contains `publication/` (39 files: 14 PDF, 14 PNG, 11 TeX) and `inputs/`.
- **Validation:** `check_run_complete()` passed. No `abort.json`.

### Run 4: PRIN Reproduction Arm (H3, H4)

- **Mode:** `prin`
- **Run Directory:** `benchmarks/results/EXP-002-r1/RUN-20261021T184600Z-e65076e-r1-reproduction-prin-cpu`
- **Command Line:**
  ```powershell
  .venv\Scripts\python -m benchmarks.campaign.exp002_r1_driver --mode prin --run-dir benchmarks/results/EXP-002-r1/RUN-20261021T184600Z-e65076e-r1-reproduction-prin-cpu --operator MichaelMaillet --source-sha e65076eb7ae97100d40ea32c60229dd40ed51033 --seed-counter 0 --seed-key 2
  ```
- **Execution Timestamp (UTC):** START `20261021T184600Z`
- **Exit Code:** `0`
- **Manifest Contents:**
  - `reproduction.json` (59,711 bytes, SHA-256 `09df73ad43144c870ad95b7fcb2a8bd02cd394549335d3a89b848b4631536771`)
  - `campaign-metadata.json` (267 bytes, SHA-256 `26bd9b4cd1ce91ee8ed17fb798ef2aa207ccbd04364fbf4f5f9583ca835eea7c`)
  - `manifest.json` (563 bytes, SHA-256 `ce7497c4b2cb5eaeb5c769da5c518d4600f5fcb2183f41f5f09de628874cd207`)
- **Retained Outputs:** `DOCS/test_and_benchmark_results/EXP-002-r1/RUN-20261021T184600Z-e65076e-r1-reproduction-prin-cpu/` contains `publication/` (39 files: 14 PDF, 14 PNG, 11 TeX) and `inputs/`.
- **Validation:** `check_run_complete()` passed. No `abort.json`.

### Run 5: Repeatability PRIN Arm (H4)

- **Mode:** `repeatability`
- **Run Directory:** `benchmarks/results/EXP-002-r1/RUN-20261021T184707Z-e65076e-r1-seedrep0-prin-cpu`
- **Command Line:**
  ```powershell
  .venv\Scripts\python -m benchmarks.campaign.exp002_r1_driver --mode repeatability --run-dir benchmarks/results/EXP-002-r1/RUN-20261021T184707Z-e65076e-r1-seedrep0-prin-cpu --operator MichaelMaillet --source-sha e65076eb7ae97100d40ea32c60229dd40ed51033 --seed-counter 0 --seed-key 2
  ```
- **Execution Timestamp (UTC):** START `20261021T184707Z`
- **Exit Code:** `0`
- **Manifest Contents:**
  - `reproduction.json` (59,708 bytes, SHA-256 `f1f5e5bcdd12714e112e22dfa058a6a37274ee8208c2dee7bb4a6cf3a4a01176`)
  - `campaign-metadata.json` (259 bytes, SHA-256 `cefdaf73760c1af0adcf7bc9f51845f0a974312483a00083578b0c4bdaf06504`)
  - `manifest.json` (563 bytes, SHA-256 `416737200c0224a2d0cf92a80a75d28737e1c94556e47b61ffe1c3a77a061729`)
- **Retained Outputs:** `DOCS/test_and_benchmark_results/EXP-002-r1/RUN-20261021T184707Z-e65076e-r1-seedrep0-prin-cpu/` contains `publication/` (39 files: 14 PDF, 14 PNG, 11 TeX) and `inputs/`.
- **Validation:** `check_run_complete()` passed. No `abort.json`.

---

## 3. Post-Execution Summary

- Total runs executed: 5
- All 5 runs exited with code 0.
- All 5 run directories verified with `check_run_complete()` and `verify_manifest()`.
- Total raw storage: 339,902 bytes (0.32 MiB, well below the 10 MiB limit).
- All 3 reproduction legs produced exactly 39 publication files and retained inputs.
- Zero predecessor files touched (`predecessor-immutability.txt`).
- Ready for handoff to E4 analysis.
