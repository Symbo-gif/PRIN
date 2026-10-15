"""Write verification/SHA256SUMS.txt for an EVIDENCE/<session>/verification directory.

Format (as EVIDENCE/0160): '<sha256> *./<posix path>' sorted by path, LF endings,
every file under the directory except SHA256SUMS.txt itself.
"""

import hashlib
import sys
from pathlib import Path

root = Path(sys.argv[1])
lines = []
for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt"):
    rel = path.relative_to(root).as_posix()
    lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()} *./{rel}")
(root / "SHA256SUMS.txt").write_bytes(("\n".join(lines) + "\n").encode("ascii"))
print(f"wrote {root / 'SHA256SUMS.txt'} with {len(lines)} entries")
