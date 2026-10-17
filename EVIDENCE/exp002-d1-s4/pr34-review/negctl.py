# The pytest plugin (kept outside the repository at run time) that drives the four negative controls by patching item.module
# copied from /c/Users/there/prin-s4-scratch/negctl.py at 2026-10-17T19:03:58Z

"""Pytest plugin (kept OUTSIDE the repository) providing four negative controls that
prove the platform-scoped digest tie in parity/test_parity_publication.py is not
vacuous.

Why the patch goes through `item.module`: `parity/` has no `__init__.py`, so pytest's
prepend import mode loads the file as the top-level module `test_parity_publication`.
An earlier version of this plugin patched `parity.test_parity_publication` instead -
a *different* module object that the collected tests never used - so the controls
silently measured nothing and reported a false pass. Patching `item.module` is
correct under any import mode, and each run prints a proof line naming the module it
actually patched.

Modes (NEGCTL env var):

  corrupt-figure       one figure's expected digest is wrong, host platform MATCHES
                       the record -> the strict branch runs -> must FAIL
  corrupt-tex          one table's expected digest is wrong, host platform MATCHES
                       -> must FAIL
  bogus+corrupt-figure the record's platform is patched to one this host is not, and
                       one figure digest is wrong -> the structural branch runs ->
                       must PASS
  bogus+corrupt-tex    platform patched away, and one TABLE digest is wrong -> tables
                       stay byte-exact off-platform -> must FAIL

The pair (corrupt-figure, bogus+corrupt-figure) is the discriminating experiment: the
identical corruption fails on the authoring platform and passes off it. The pair
(corrupt-tex, bogus+corrupt-tex) proves the tables were not relaxed along with the
figures.

Corruption targets are discovered from the frozen record itself, never hard-coded.
No repository file is edited.
"""

from __future__ import annotations

import os

MODE = os.environ.get("NEGCTL", "")
BOGUS = "Linux-9.9.9-bogus-x86_64-with-glibc"
VALID = {
    "corrupt-figure",
    "corrupt-tex",
    "bogus+corrupt-figure",
    "bogus+corrupt-tex",
}
_patched: set[int] = set()


def _apply(gate) -> None:  # noqa: ANN001 - pytest plugin, module object
    """Patch the collected test module in place, once."""
    if id(gate) in _patched:
        return
    _patched.add(id(gate))

    original = gate._e3_files
    real = sorted(original(gate._E3_REFERENCE_RUN))
    tex = next(n for n in real if n.endswith(".tex"))
    fig = next(n for n in real if n.endswith(".png"))
    target = fig if MODE.endswith("corrupt-figure") else tex

    if MODE.startswith("bogus"):
        gate._e3_platform = lambda run: BOGUS  # type: ignore[method-assign]

    def corrupted(run: str) -> dict:  # noqa: ANN202
        files = dict(original(run))
        if target not in files:
            raise AssertionError(
                f"negative control target {target!r} is not in the E3 record; "
                f"available sample: {sorted(files)[:3]}"
            )
        files[target] = dict(files[target])
        files[target]["normalized_sha256"] = "0" * 64
        return files

    gate._e3_files = corrupted  # type: ignore[method-assign]
    print(
        f"# NEGCTL {MODE}: patched module {gate.__name__} (id={id(gate)}); "
        f"corrupted the recorded digest of {target}"
        + ("; record platform forced to " + BOGUS if MODE.startswith("bogus") else "")
    )


def pytest_runtest_setup(item) -> None:  # noqa: ANN001
    """Patch the module object pytest actually collected, before each test runs."""
    if not MODE:
        return
    gate = getattr(item, "module", None)
    if gate is not None:
        _apply(gate)


def pytest_configure() -> None:
    """Announce the selected mode once, before collection."""
    if not MODE:
        return
    if MODE not in VALID:
        raise SystemExit(f"unknown NEGCTL mode {MODE!r}; expected one of {sorted(VALID)}")
    print(f"# NEGCTL selected: {MODE}")
