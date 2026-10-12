"""Reconstruct validator revision 1 from revision 2 by inverting the two recorded edits.

The result is accepted only if its SHA-256 equals the digest recorded in log.md
(5703fad41b5bf8466643694cc9a711ee423012762992bb2def1eb8074964fd4d).
"""

import hashlib
import sys
from pathlib import Path

scratch = Path(sys.argv[1])
rev2 = (scratch / "validate_run_record.py").read_bytes()
text = rev2.decode("utf-8")
crlf = "\r\n" in text
nl = "\r\n" if crlf else "\n"

wrapper = nl.join(
    [
        "def main() -> int:",
        '    """Run every check; an unexpected error is a FAIL, never a silent crash."""',
        "    try:",
        "        return _run()",
        "    except Exception as exc:  # noqa: BLE001 - a crash must not look like a pass",
        '        check("Z0 validator completed without an unexpected error", False, repr(exc))',
        "        return finish()",
        "",
        "",
        "def _run() -> int:",
        "",
    ]
)
assert wrapper in text, "wrapper block not found"
rev1 = text.replace(wrapper, nl.join(["def main() -> int:", ""]), 1)
rev1 = rev1.replace(
    'raise RuntimeError("cannot parse the registered stems from the protocol blob")',
    'raise SystemExit("cannot parse the registered stems from the protocol blob")',
)
rev1 = rev1.replace(
    'raise RuntimeError("reference __init__ blob digest is not the pinned digest")',
    'raise SystemExit("reference __init__ blob digest is not the pinned digest")',
)
rev1 = rev1.replace(
    'raise RuntimeError("reference literal __all__ missing")',
    'raise SystemExit("reference literal __all__ missing")',
)
out = rev1.encode("utf-8")
digest = hashlib.sha256(out).hexdigest()
print("reconstructed rev1 sha256:", digest)
print("expected (log.md)        :", "5703fad41b5bf8466643694cc9a711ee423012762992bb2def1eb8074964fd4d")
print("line endings crlf =", crlf)
if digest == "5703fad41b5bf8466643694cc9a711ee423012762992bb2def1eb8074964fd4d":
    (scratch / "validate_run_record.rev1.py").write_bytes(out)
    print("MATCH - wrote validate_run_record.rev1.py")
    sys.exit(0)
print("NO MATCH - not writing")
sys.exit(1)
