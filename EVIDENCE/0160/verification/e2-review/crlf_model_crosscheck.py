"""Cross-check the Lean models in ``CrlfCanonical.lean`` against real Python.

Exhaustively over every string of length <= 9 on the alphabet {CR, LF, 'A'}:

* ``canon`` (the Lean definition, transcribed) equals the driver's actual
  operation ``bytes.replace(b"\\r\\n", b"\\n")``;
* ``translate`` equals what CPython's text-mode ``open(path, "w")`` (the pinned
  reference writer's mode, ``newline=None``) writes on this host — run on the
  Windows host this experiment is registered for, where ``os.linesep`` is
  CR LF;
* the theorem's statement holds on the real operations.
"""

from __future__ import annotations

import itertools
import os
import tempfile
from pathlib import Path

ALPHABET = (13, 10, 65)


def canon(s: list[int]) -> list[int]:
    out: list[int] = []
    i = 0
    while i < len(s):
        if s[i] == 13 and i + 1 < len(s) and s[i + 1] == 10:
            out.append(10)
            i += 2
        else:
            out.append(s[i])
            i += 1
    return out


def translate(s: list[int]) -> list[int]:
    out: list[int] = []
    for b in s:
        out.extend((13, 10) if b == 10 else (b,))
    return out


assert os.linesep == "\r\n", "run on the registered Windows host"
checked = 0
with tempfile.TemporaryDirectory() as tmp:
    target = Path(tmp) / "t.tex"
    for n in range(10):
        for combo in itertools.product(ALPHABET, repeat=n):
            s = list(combo)
            raw = bytes(s)
            assert bytes(canon(s)) == raw.replace(b"\r\n", b"\n"), s
            with open(target, "w", encoding="utf-8") as stream:  # as _save_table
                stream.write(raw.decode("latin-1"))
            written = target.read_bytes()
            assert written == bytes(translate(s)), s
            assert written.replace(b"\r\n", b"\n") == raw, s
            checked += 1
print(f"RESULT: {checked} strings; canon == bytes.replace, translate == "
      "Windows text-mode write, canon(translate(x)) == x on real I/O")
