# .github/workflows/ — hosted CI/CD gates

| Workflow | Current role |
|---|---|
| `rust.yml` | Formatting, Clippy, cross-platform tests, rustdoc, and Cargo Audit |
| `python.yml` | Lint/type/doc/security gates and Python 3.11–3.13 Linux/Windows tests |
| `parity.yml` | Differential corpus gate; safely skips before WP-002 defines cases |
| `gpu.yml` | Opt-in self-hosted GPU validation |
| `repro.yml` | Explicitly guarded until WP-035 owns executable reproduction |
| `release.yml` | Wheel/sdist release path; crate publication guarded until WP-005 |
| `snyk.yml` | Snyk Code plus required full-history Gitleaks secret scanning |

`main` requires the applicable checks. Native GitHub secret scanning is currently
unavailable for this private repository, so plan amendment #5 governs the
required Gitleaks and branch-protection substitute until native controls become
available.
