# `ci/` — CI configuration artefacts

Committed configuration consumed by `.github/workflows/*` and by the
maintainer when provisioning repository settings. Introduced by the ETCA-002
remediation session (2026-09-02, Project Plan amendment #45).

## `lint-constraints.txt`

Pinned toolchain for `python.yml`'s `lint` job (ETCA-002 T-F2 / T-F10 /
governance G6). No merge-gating CI job may `pip install` an unpinned tool —
before this file the `lint` job's `mypy` / `torch` floated run-to-run and
`mypy --strict` was green locally and red in CI on the same commit. Bump the
pins deliberately, in their own commit, keeping them in step with the
maintainer `.venv`.

## `main-branch-ruleset.json`

The `main` branch **ruleset** payload (ETCA-002 T-F7 / governance G3). Classic
branch protection is unavailable on this private repository
(`gh api repos/Symbo-gif/PRIN/branches/main/protection` → `404 "Branch
protection has been disabled"` — DV-009 precedent), so a ruleset is the
mechanism. Apply / update it with:

```bash
# create (first time)
gh api -X POST repos/Symbo-gif/PRIN/rulesets --input ci/main-branch-ruleset.json
# update (subsequent) — RULESET_ID from `gh api repos/Symbo-gif/PRIN/rulesets`
gh api -X PUT repos/Symbo-gif/PRIN/rulesets/RULESET_ID --input ci/main-branch-ruleset.json
```

Every workflow whose job context is in the required set must run on **every**
PR (no `pull_request` `paths:` filter) — a filtered required check stays
permanently "expected" and blocks the merge on any PR that doesn't touch its
paths. `parity.yml` and `repro.yml` had such filters; they were removed when
`parity` / `reproduce` were made required.

It enforces, with **no bypass actors** (`enforce_admins` equivalent):

- a pull request before merging (`0` required approvals — the gate is CI, not
  review, for this single-maintainer repo);
- every workflow's status checks green, **including `gpu-cuda` / `gpu-wgpu`**
  (maintainer decision 2026-09-02, promoted per **DV-034** — GPU validation is
  a hard merge gate);
- no force-pushes, no branch deletion.

**Operational note:** `gpu-cuda` / `gpu-wgpu` run only on the self-hosted
`PRIN-GPU-Runner` (`[self-hosted, gpu]`), the DV-024 single point of failure.
While that runner is offline, PRs to `main` **cannot merge** until it returns.
This is the accepted cost of making GPU validation a required check.

## `install-gpu-runner-service.ps1`

One-shot fix for the chronic `PRIN-GPU-Runner` offline condition (DV-024).
Diagnosed 2026-09-02: the runner was never installed as a Windows service —
it only ran interactively (`C:\actions-runner\run.cmd`), so it stopped every
time the terminal closed or the machine rebooted/slept. Run this **once, from
an elevated PowerShell** (with `gh` authenticated):

```powershell
powershell -ExecutionPolicy Bypass -File ci/install-gpu-runner-service.ps1
```

It removes the interactive registration, re-registers the runner as an
**auto-start service** (running as the desktop user so rustup / miniforge /
CUDA stay on PATH), and disables AC-power sleep. After that the runner
survives reboots unattended. Register a **second** GPU runner to remove the
SPOF entirely (DV-034).
