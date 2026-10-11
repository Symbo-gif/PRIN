"""Defect-catching proof for the PR #32 review-round regression tests.

Each new/strengthened test is run (a) against the pre-fix state or a
synthetic mutation of the evidence/config it guards - it must FAIL - and
(b) against the real repository state or a benign variant - it must PASS.
Nothing under the repository is modified: pre-fix inputs come from
`git show add7386a:<path>` into a temp directory and are injected by
monkeypatching module globals.
"""

import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(r"C:\dev\PRIN")
sys.path.insert(0, str(REPO))


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "tests" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git_show(rev_path: str) -> bytes:
    return subprocess.check_output(["git", "show", rev_path], cwd=REPO)


results = []


def expect(label: str, fn, should_fail: bool) -> None:
    try:
        fn()
        outcome = "PASS"
    except AssertionError as exc:
        first = (str(exc).splitlines() or ["<no message>"])[0]
        outcome = "FAIL (AssertionError: " + first[:110] + ")"
    ok = (outcome.startswith("FAIL")) == should_fail
    results.append(ok)
    want = "must FAIL" if should_fail else "must PASS"
    print(f"[{'ok' if ok else 'UNEXPECTED'}] {label:<66} {want:<10} -> {outcome}")


gates = load("test_campaign_quality_gates")
manifest = load("test_ea007_manifest")
tmp = Path(tempfile.mkdtemp(prefix="pr32proof-"))
NL = chr(10)
FENCE = chr(96) * 3

# --- PR32-F1: AGENTS.md PowerShell block ------------------------------------
old_agents = tmp / "AGENTS.old.md"
old_agents.write_bytes(git_show("add7386a:AGENTS.md"))
real_agents = gates.AGENTS
fn1 = gates.test_agents_powershell_block_has_no_embedded_double_quotes
gates.AGENTS = old_agents
expect("F1 quoting test vs add7386a AGENTS.md", fn1, True)
gates.AGENTS = real_agents
expect("F1 quoting test vs working-tree AGENTS.md", fn1, False)


def agents_with(line: str, newline: str = NL) -> Path:
    path = tmp / f"AGENTS.{abs(hash((line, newline)))}.md"
    body = FENCE + "powershell" + NL + line + NL + FENCE + NL
    path.write_bytes(body.replace(NL, newline).encode("utf-8"))
    return path


gates.AGENTS = agents_with("tool 'a' \"b\" 'c'")
expect("F1 quoting test: `cmd 'a' \"b\" 'c'` is NOT a false fail", fn1, False)
gates.AGENTS = agents_with("tool --config \"include = ['*.py']\"")
expect("F1 quoting test: TOML-literal form passes", fn1, False)
gates.AGENTS = agents_with("tool --config 'include = [\"*.py\"]'")
expect("F1 quoting test: double quote inside single quotes fails", fn1, True)
gates.AGENTS = agents_with("tool 'a' --config 'x = \"y\"' 'c'")
expect("F1 quoting test: bad segment between good ones fails", fn1, True)
gates.AGENTS = agents_with("tool --config \"include = ['*.py']\"", newline=chr(13) + chr(10))
expect("F1 quoting test: CRLF checkout (universal newlines)", fn1, False)
gates.AGENTS = agents_with("# don't use \"foo\" with 'bar'" + NL + "tool 'ok'")
expect("F1 quoting test: an apostrophe in a comment line is not a segment", fn1, False)
gates.AGENTS = agents_with('tool --config "a ""b"" c"')
expect('F1 quoting test: PowerShell doubled-quote escape inside "..."', fn1, False)
gates.AGENTS = real_agents

# --- PR32-F9: rustdoc leg (hosted + local) ----------------------------------
fn9 = gates.test_rustdoc_gate_documents_the_feature_gated_gpu_module
real_root = gates.REPO_ROOT
real_rust = (REPO / ".github" / "workflows" / "rust.yml").read_text(encoding="utf-8")


def with_rust_yml(text: str) -> None:
    root = tmp / f"repo{abs(hash(text))}"
    (root / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
    (root / ".github" / "workflows" / "rust.yml").write_text(text, encoding="utf-8")
    gates.REPO_ROOT = root


with_rust_yml(git_show("add7386a:.github/workflows/rust.yml").decode("utf-8"))
expect("F9 rustdoc test vs add7386a rust.yml (no leg)", fn9, True)
with_rust_yml(real_rust)
expect("F9 rustdoc test vs working-tree rust.yml + AGENTS.md", fn9, False)
with_rust_yml(real_rust.replace("--features cpu", "--features strict-checks"))
expect("F9 rustdoc test: non-backend feature `strict-checks`", fn9, True)
with_rust_yml(real_rust.replace("--features cpu", "--features wgpu,strict-checks"))
expect("F9 rustdoc test: backend feature inside a list is accepted", fn9, False)
no_env = real_rust.replace(
    'RUSTDOCFLAGS: "-D warnings"', 'OTHER_FLAG: "x"  # RUSTDOCFLAGS -D warnings'
)
with_rust_yml(no_env)
expect("F9 rustdoc test: job env lost, a comment still mentions it", fn9, True)
job_env = '    env:\n      RUSTDOCFLAGS: "-D warnings"\n    steps:\n'
assert job_env in real_rust
moved = real_rust.replace(job_env, "    steps:\n").replace(
    "        run: cargo doc --workspace --no-deps\n",
    "        run: cargo doc --workspace --no-deps\n"
    '        env:\n          RUSTDOCFLAGS: "-D warnings"\n',
)
with_rust_yml(moved)
expect("F9 rustdoc test: flag moved to ANOTHER step's env (prin-sim step unflagged)", fn9, True)
with_rust_yml(real_rust.replace('RUSTDOCFLAGS: "-D warnings"', "RUSTDOCFLAGS: '-D warnings'"))
expect("F9 rustdoc test: YAML single-quoted flag value is accepted", fn9, False)
with_rust_yml(
    real_rust.replace(
        "-p prin-sim --no-deps --features cpu", "--package prin-sim --no-deps --features=cpu"
    )
)
expect("F9 rustdoc test: `--package prin-sim` and `--features=cpu` spellings", fn9, False)
with_rust_yml(
    real_rust.replace("-p prin-sim --no-deps --features cpu", "-p prin-sim --no-deps -F cpu")
)
expect("F9 rustdoc test: `-F cpu` spelling", fn9, False)
with_rust_yml(
    real_rust.replace(
        "-p prin-sim --no-deps --features cpu",
        "-p prin-sim --features strict-checks --features cpu",
    )
)
expect("F9 rustdoc test: a repeated --features flag is read in full", fn9, False)
with_rust_yml(
    real_rust
    + "\n  docs2:\n    runs-on: ubuntu-latest\n    steps:\n"
    + "      - run: cargo doc -p prin-sim --no-deps --features cpu\n"
)
expect("F9 rustdoc test: a SECOND job runs the leg without the job-level flag", fn9, True)
with_rust_yml(
    real_rust.replace(
        job_env,
        '    env:  # doc flags\n\n      # strict\n      RUSTDOCFLAGS: "-D warnings"\n    steps:\n',
    )
)
expect("F9 rustdoc test: a comment/blank line inside the job-level env block", fn9, False)
gates.REPO_ROOT = real_root
reordered = tmp / "AGENTS.reordered.md"
reordered.write_text(
    real_agents.read_text(encoding="utf-8").replace(
        "cargo doc -p prin-sim --no-deps --features cpu",
        "cargo doc --no-deps --package prin-sim --features cpu",
    ),
    encoding="utf-8",
)
gates.AGENTS = reordered
expect("F9 rustdoc test: AGENTS.md line with `--package` and reordered options", fn9, False)
gates.AGENTS = real_agents
no_local = tmp / "AGENTS.nolocal.md"
no_local.write_text(
    "".join(
        line
        for line in real_agents.read_text(encoding="utf-8").splitlines(keepends=True)
        if "cargo doc -p prin-sim" not in line
    ),
    encoding="utf-8",
)
gates.AGENTS = no_local
expect("F9 rustdoc test: AGENTS.md local leg deleted", fn9, True)
gates.AGENTS = real_agents

# --- PR32-F12: duplicate campaign module names ------------------------------
fn12 = gates.test_campaign_analysis_script_basenames_are_unique
real_campaign = gates.CAMPAIGN_ROOT


def campaign_tree(name: str, files: dict[str, str]) -> Path:
    root = tmp / name
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


gates.CAMPAIGN_ROOT = campaign_tree(
    "dup", {"EXP-A/analysis/quality.py": "x = 1\n", "EXP-B/analysis/quality.py": "y = 2\n"}
)
expect("F12 module-name test: two campaigns sharing quality.py", fn12, True)
gates.CAMPAIGN_ROOT = campaign_tree(
    "pkgdup", {"EXP-A/analysis/util/__init__.py": "", "EXP-B/analysis/util/__init__.py": ""}
)
expect("F12 module-name test: both ship package `util` (real duplicate)", fn12, True)
gates.CAMPAIGN_ROOT = campaign_tree(
    "pkgok", {"EXP-A/analysis/pkg_a/__init__.py": "", "EXP-B/analysis/pkg_b/__init__.py": ""}
)
expect("F12 module-name test: differently named packages (no false fail)", fn12, False)
gates.CAMPAIGN_ROOT = campaign_tree(
    "pyidup", {"EXP-A/analysis/runner.py": "x = 1\n", "EXP-B/analysis/runner.pyi": "x: int\n"}
)
expect("F12 module-name test: a stub in another campaign duplicates the module", fn12, True)
gates.CAMPAIGN_ROOT = campaign_tree(
    "pyipair", {"EXP-A/analysis/runner.py": "x = 1\n", "EXP-A/analysis/runner.pyi": "x: int\n"}
)
expect("F12 module-name test: a module beside its own stub is one module", fn12, False)
gates.CAMPAIGN_ROOT = campaign_tree(
    "stubdup", {"EXP-A/analysis/stubs/__init__.pyi": "", "EXP-B/analysis/stubs/__init__.pyi": ""}
)
expect("F12 module-name test: both ship a stub-only package `stubs`", fn12, True)
gates.CAMPAIGN_ROOT = campaign_tree(
    "stubok", {"EXP-A/analysis/sa/__init__.pyi": "", "EXP-B/analysis/sb/__init__.pyi": ""}
)
expect("F12 module-name test: differently named stub-only packages (no false fail)", fn12, False)
gates.CAMPAIGN_ROOT = real_campaign
expect("F12 module-name test vs real DOCS/experiments", fn12, False)

# --- PR32-F15: urllib3 floor test --------------------------------------------
fn15 = gates.test_sphinx_requirements_urllib3_minimum_patched


def with_requirements(text: str) -> None:
    root = tmp / f"req{abs(hash(text))}"
    (root / "DOCS" / "sphinx").mkdir(parents=True, exist_ok=True)
    (root / "DOCS" / "sphinx" / "requirements.txt").write_text(text, encoding="utf-8")
    gates.REPO_ROOT = root


with_requirements("sphinx>=7" + NL + "urllib3>=2.8.0" + NL)
expect("F15 urllib3 test: a plain >=2.8.0 floor", fn15, False)
with_requirements("urllib3>=2.8.0  # CVE-2026-97687/-88/-89" + NL)
expect("F15 urllib3 test: trailing CVE comment is tolerated (old regex failed)", fn15, False)
with_requirements("urllib3>=2.7.0" + NL)
expect("F15 urllib3 test: the vulnerable 2.7.0 floor fails", fn15, True)
with_requirements("# urllib3>=2.8.0" + NL)
expect("F15 urllib3 test: a commented-out entry cannot satisfy it", fn15, True)
with_requirements("urllib3>=2.8.0" + NL + "urllib3>=2.0.0" + NL)
expect("F15 urllib3 test: every match is checked, not just the first", fn15, True)
with_requirements("urllib3>=2.8.0,<3" + NL)
expect("F15 urllib3 test: a compound specifier `>=2.8.0,<3` is accepted", fn15, False)
with_requirements("urllib3>=2.8.0; python_version >= '3.9'" + NL)
expect("F15 urllib3 test: an environment marker is accepted", fn15, False)
with_requirements("urllib3>=2.7.0,<3" + NL)
expect("F15 urllib3 test: a vulnerable floor with an upper bound still fails", fn15, True)
with_requirements("urllib3<3,>=2.8.0" + NL)
expect("F15 urllib3 test: specifier order is irrelevant (`<3,>=2.8.0`)", fn15, False)
with_requirements("urllib3>=2.8" + NL)
expect("F15 urllib3 test: a two-segment floor `>=2.8`", fn15, False)
with_requirements("urllib3[brotli]>=2.8.0" + NL)
expect("F15 urllib3 test: an extras requirement", fn15, False)
with_requirements("urllib3" + NL)
expect("F15 urllib3 test: an unpinned requirement admits the vulnerable release", fn15, True)
gates.REPO_ROOT = real_root
expect("F15 urllib3 test vs the real DOCS/sphinx/requirements.txt", fn15, False)

# --- PR32-F14: bandit exclusion truth table ---------------------------------
good = ["tests/*", "*/tests/*", "benchmarks/*", "*/benchmarks/*", "parity/*", "*/parity/*"]
fn14 = gates.test_bandit_exclusions_are_component_globs
expect("F14 truth table vs the shipped-shape list", lambda: fn14(good), False)
for label, bad in {
    "escaping glob `../../*` (old suffix check passed it)": good + ["../../*"],
    "top-level glob without its `*/d/*` twin": good + ["zzz/*"],
    "substring-style glob `*parity*/*`": good + ["*parity*/*"],
    "Windows spelling `.venv\\*`": good + [".venv\\*"],
    "required component `parity` dropped": [g for g in good if "parity" not in g],
}.items():
    old_shape_passes = all(p.endswith("/*") or p.endswith(chr(92) + "*") for p in bad)
    expect(f"F14 truth table vs {label}", lambda b=bad: fn14(b), True)
    print(
        f"      (pre-change suffix-only check would have {'PASSED' if old_shape_passes else 'failed'} this list)"
    )

# --- PR32-F7: executable manifest -------------------------------------------
src = REPO / "EVIDENCE" / "ea007"
real_ev, real_man = manifest.EVIDENCE_ROOT, manifest.MANIFEST
t_digest = manifest.test_every_manifest_entry_matches_the_committed_bytes
t_cover = manifest.test_manifest_covers_every_evidence_file
t_track = manifest.test_every_hashed_evidence_file_is_tracked_by_git


def point_at(copy: Path) -> None:
    manifest.EVIDENCE_ROOT = copy
    manifest.MANIFEST = copy / "verification" / "SHA256SUMS.txt"


def fresh_copy(name: str) -> Path:
    dst = tmp / name
    shutil.copytree(src, dst)
    return dst


expect("F7 digest test vs real committed evidence (matches)", t_digest, False)
expect("F7 coverage test vs real committed evidence (complete)", t_cover, False)

c1 = fresh_copy("ev-corrupt")
log = c1 / "verification" / "full-gate" / "25-pytest-final.log"
log.write_bytes(log.read_bytes().replace(NL.encode(), (chr(13) + NL).encode(), 1))
point_at(c1)
expect("F7 digest test vs one drifted byte (the 0738714 failure)", t_digest, True)

c2 = fresh_copy("ev-extra")
(c2 / "verification" / "full-gate" / "99-extra.log").write_text("not in manifest\n")
point_at(c2)
expect("F7 coverage test vs an evidence file the manifest omits", t_cover, True)
(c2 / "verification" / "full-gate" / "99-extra.log").unlink()
(c2 / ".DS_Store").write_bytes(b"\x00")
(c2 / "verification" / "Thumbs.db").write_bytes(b"\x00")
(c2 / "verification" / "notes.txt.swp").write_bytes(b"\x00")
expect("F7 coverage test tolerates OS junk (.DS_Store, Thumbs.db, *.swp)", t_cover, False)
(c2 / "README.md").unlink()
expect("F7 coverage test: the unhashed-by-design README.md deleted", t_cover, True)

c3 = fresh_copy("ev-missing")
(c3 / "verification" / "full-gate" / "01-ruff-check.log").unlink()
point_at(c3)
expect("F7 digest test vs a manifest entry whose file is gone", t_digest, True)

c4 = fresh_copy("ev-escape")
man = c4 / "verification" / "SHA256SUMS.txt"
man.write_bytes(man.read_bytes() + b"0" * 64 + b" *../../pyproject.toml\n")
point_at(c4)
expect("F7 digest test vs a path escaping EVIDENCE/ea007/", t_digest, True)

c5 = fresh_copy("ev-malformed")
man = c5 / "verification" / "SHA256SUMS.txt"
man.write_bytes(man.read_bytes() + b"not a digest line\n")
point_at(c5)
expect("F7 digest test vs a malformed manifest line", t_digest, True)

c6 = fresh_copy("ev-case")
man = c6 / "verification" / "SHA256SUMS.txt"
man.write_bytes(man.read_bytes().replace(b"GATE-STATUS.md", b"gate-status.md"))
point_at(c6)
expect("F7 digest test vs wrong letter case (fails on Windows too)", t_digest, True)

c7 = fresh_copy("ev-dup")
man = c7 / "verification" / "SHA256SUMS.txt"
first = man.read_bytes().splitlines()[0]
man.write_bytes(man.read_bytes() + first + b"\n")
point_at(c7)
expect("F7 digest test vs a duplicated manifest line", t_digest, True)

manifest.EVIDENCE_ROOT, manifest.MANIFEST = real_ev, real_man
real_tracked_fn = manifest._git_tracked
expect("F7 tracked-by-git test vs the real index (everything tracked)", t_track, False)
tracked_now = real_tracked_fn()
victim = "verification/post-commit/gitleaks-final-add7386.log"
manifest._git_tracked = lambda: tracked_now - {victim}
expect("F7 tracked-by-git test vs a hashed-but-untracked log (ignored *.log)", t_track, True)
manifest._git_tracked = real_tracked_fn

shutil.rmtree(tmp, ignore_errors=True)
print()
print(f"{sum(results)}/{len(results)} expectations met")
sys.exit(0 if all(results) else 1)
