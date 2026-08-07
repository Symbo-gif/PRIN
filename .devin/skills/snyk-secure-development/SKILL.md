---
name: snyk-secure-development
description: Enforce PRIN secure-at-inception scanning and evidence for source or dependency changes
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - find_file_by_name
  - exec
  - edit
  - write
  - mcp_list_tools
  - mcp_call_tool
  - todo_write
---

# Snyk secure development

Apply Coding Standards §6 without weakening any existing gate.

1. Identify changed first-party source and dependency manifests. Exclude only
   the reviewed historical material covered by the repository `.snyk` policy.
2. Before using Snyk MCP in a session, discover the `snyk` server tools. Confirm
   authentication and trust without exposing credentials.
3. Run Snyk Code for new or modified code in supported languages. Run Snyk Open
   Source for supported dependency inputs. When a native manifest is unsupported,
   use the governed resolved-manifest or SBOM path if available and retain the
   ecosystem-native audit as authoritative.
4. Run every applicable native control, including `cargo audit`, `pip-audit`,
   Ruff security rules, Bandit, and GitHub hosted secret controls.
5. Remediate findings attributable to the change, then rescan until the governed
   threshold is clean. Never add an ignore, exclusion, or suppression without an
   evidence-backed approved deviation or amendment.
6. Report the scan type, scope, threshold, and result. If a scan is unavailable,
   report it as blocked; never claim success or emit an unverifiable badge.
