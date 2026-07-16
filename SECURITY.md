# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 0.x (pre-release) | Latest release only |

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
- `unsafe` Rust is forbidden outside audited kernel-FFI modules
  (`#![forbid(unsafe_code)]` elsewhere) — see the Coding Standards.
- CI runs `cargo audit`, `pip-audit`, and secret scanning on every push.
- Model files (`models/*.onnx`) are validated against a SHA-256 manifest by the
  reproducibility pipeline.
