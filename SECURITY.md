# Security Policy

## Supported Versions

The Rust workspace and the Python package share one version (Versioning and
Release Standards §1). The current pre-release is `1.0.0-rc1` (Rust / SemVer)
and `1.0.0rc1` (Python / PEP 440). `1.0.0` has not shipped.

| Version | Supported |
|---|---|
| Latest `1.0.0-rc*` pre-release | Yes |
| Earlier `0.x` pre-releases | No |
| `1.0.0` and later | Latest stable release only, once published |

Until `1.0.0` ships, security fixes target the latest pre-release. After
`1.0.0` is published, only the latest stable release is supported. Security
patches use the post-release hotfix workflow and are announced with GitHub
Security Advisories (Versioning and Release Standards §7).

## Reporting a Vulnerability

Please **do not** open a public issue for security vulnerabilities.

Email **therealmichaelmaillet@gmail.com** with:
- A description of the vulnerability and its impact
- Steps to reproduce or a proof of concept
- Affected versions and platforms

You will receive an acknowledgement within 72 hours and a remediation plan or
status update within 14 days.

## Scope and Hardening

- PRIN performs **no runtime code generation** (kernels are precompiled at
  wheel-build time), eliminating the JIT attack surface present in PRINet 3.0.
- `unsafe` Rust is forbidden (`#![forbid(unsafe_code)]`) except in audited
  kernel-FFI modules inside `prin-kernels` and audited Python-FFI modules
  inside `prin-py` — see Coding Standards §6.1.
- CI runs `cargo audit` and `pip-audit` (Coding Standards §6.2). Secret
  scanning in that section requires native GitHub secret scanning and push
  protection. While GitHub reports native scanning unavailable, the approved
  substitute is a blocking full-history secret scan on every push and pull
  request (plan amendment #5; the Gitleaks job in `.github/workflows/snyk.yml`).
  Snyk does not replace those gates.
- Model files (`models/*.onnx`) are validated against a SHA-256 manifest by the
  reproducibility pipeline.
