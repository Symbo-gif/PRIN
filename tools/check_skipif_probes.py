#!/usr/bin/env python3
"""Fail when a ``skipif`` guard probes provider *registration*, not executability.

ETCA-002 finding T-F3 / governance G8. T-F3 is the recurrence of ETCA-001 T-F2:
a ``@pytest.mark.skipif`` predicate that reads
``"<EP>" in onnxruntime.get_available_providers()`` tests whether an execution
provider is *compiled into the wheel*, not whether it can *execute a graph on
this host* — so it does not fire on a GitHub-hosted runner that has
``onnxruntime-directml`` installed with no DirectML device, and the guarded
test runs and hard-fails.

When an audit finding recurs after its remediation was signed off, the
remediation must add a regression guard for the *class*, not just fix the
instance (methodology §4). This is that guard, run by ``python.yml``'s
``governance`` job.

Allowed: ``torch.cuda.is_available()`` (a genuine device probe — the
``tests/README.md`` reference guard) and any use inside
``tests/_env.py``, where the executability probes are centralised.

Exit codes:

- ``0`` — no registration-probe ``skipif`` guards found.
- ``1`` — one or more found.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_TESTS = Path(__file__).resolve().parents[1] / "tests"
_ALLOW_FILES = {"_env.py"}
_BANNED = re.compile(r"get_available_providers\s*\(")
_SKIPIF_NEAR = re.compile(r"skipif|importorskip", re.IGNORECASE)


def scan() -> list[str]:
    """Return a list of ``path:line`` offences."""
    offences: list[str] = []
    for path in sorted(_TESTS.rglob("test_*.py")):
        if path.name in _ALLOW_FILES:
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            if not _BANNED.search(line):
                continue
            # A registration probe is only a problem when it gates collection.
            window = "\n".join(lines[max(0, i - 3) : i + 2])
            if _SKIPIF_NEAR.search(window):
                rel = path.relative_to(_TESTS.parent)
                offences.append(f"{rel}:{i + 1}: {line.strip()}")
    return offences


def main() -> int:
    """Run the scan and report."""
    offences = scan()
    if not offences:
        print("check_skipif_probes: no registration-probe skipif guards")
        return 0
    print("check_skipif_probes: FAIL — skipif guards probing provider registration:")
    for offence in offences:
        print(f"  {offence}")
    print(
        "\nUse an executability probe instead (tests/_env.py::directml_executes) — "
        "see ETCA-002 T-F3 / governance G8."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
