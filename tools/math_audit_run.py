"""Executive Mathematical Audit runner.

Runs every claim ledger under `tools/math_audit_claims/` through the external
`math-audit-mcp` tool's `audit_claim_ledger`, using PRIN's own policy profile
(`tools/math_audit_policy.yaml`), and writes a consolidated gate report to
`EVIDENCE/math-audit/`. See
`DOCS/standards/Executive_Mathematical_Audit_Governance_and_Methodology.md`.

`math-audit-mcp` is an external tool, not vendored into this repository (same
posture as Snyk/`cargo-audit`/`pip-audit`); its installation is located via
`MATH_AUDIT_MCP_HOME`, defaulting to the maintainer workstation path recorded
in the governance doc.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_MCP_HOME = r"C:\dev\--DEV\Math Audit MCP"
_DEFAULT_OUTPUT = _REPO_ROOT / "EVIDENCE" / "math-audit" / "ema-run-summary.json"


def _load_mcp_home() -> Path:
    home = Path(os.environ.get("MATH_AUDIT_MCP_HOME", _DEFAULT_MCP_HOME))
    src = home / "src"
    if not src.is_dir():
        raise SystemExit(
            f"math-audit-mcp not found at {home} (src/ missing). "
            "Set MATH_AUDIT_MCP_HOME to the tool's repository root."
        )
    sys.path.insert(0, str(src))
    return home


def main(argv: list[str] | None = None) -> int:
    """Run every PRIN claim ledger through math-audit-mcp and report the result."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--claims-dir",
        type=Path,
        default=_REPO_ROOT / "tools" / "math_audit_claims",
        help="Directory of claim ledger JSON files.",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=_REPO_ROOT / "tools" / "math_audit_policy.yaml",
        help="PRIN math-audit-mcp policy file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help="Path where the consolidated gate report JSON will be written.",
    )
    args = parser.parse_args(argv)

    _load_mcp_home()

    from math_audit_mcp import __version__ as tool_version  # type: ignore[import-not-found]
    from math_audit_mcp.config import RuntimeConfig, load_policy  # type: ignore[import-not-found]
    from math_audit_mcp.policies.engine import PolicyEngine  # type: ignore[import-not-found]
    from math_audit_mcp.schemas.requests import (  # type: ignore[import-not-found]
        AuditClaimLedgerRequest,
    )
    from math_audit_mcp.tools import audit_claim_ledger  # type: ignore[import-not-found]

    output_root = _REPO_ROOT / "EVIDENCE" / "math-audit"
    output_root.mkdir(parents=True, exist_ok=True)

    runtime = RuntimeConfig.from_env(
        {
            "MATH_AUDIT_POLICY_PATH": str(args.policy),
            "MATH_AUDIT_ALLOWED_ROOTS": str(_REPO_ROOT),
            "MATH_AUDIT_OUTPUT_ROOT": str(output_root),
        }
    )
    policy = load_policy(runtime)
    engine = PolicyEngine(policy)

    ledger_files = sorted(args.claims_dir.glob("*.json"))
    if not ledger_files:
        raise SystemExit(f"No claim ledgers found under {args.claims_dir}")

    results: list[dict[str, object]] = []
    any_non_pass = False
    for path in ledger_files:
        req = AuditClaimLedgerRequest(ledger_path=str(path))
        try:
            manifest, bundle_dir = audit_claim_ledger.run(req, engine, output_root)
            status = manifest.overall_status
            results.append(
                {
                    "ledger": path.name,
                    "overall_status": status,
                    "bundle_path": str(bundle_dir),
                }
            )
        except Exception as exc:  # pragma: no cover -- gate script, fail loud
            status = f"ERROR: {exc}"
            results.append({"ledger": path.name, "overall_status": status, "bundle_path": None})
        if status != "PASS":
            any_non_pass = True
        print(f"{path.name}: {status}")

    report = {
        "tool_version": tool_version,
        "policy_path": str(args.policy),
        "policy_snapshot_hash": engine.snapshot_hash,
        "output_root": str(output_root),
        "ledgers": results,
        "gate_pass": not any_non_pass,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Consolidated report written to: {args.output}")
    return 0 if not any_non_pass else 1


if __name__ == "__main__":
    sys.exit(main())
