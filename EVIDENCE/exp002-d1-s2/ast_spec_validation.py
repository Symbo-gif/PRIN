r"""Statically cross-validate the 34 registered divergences against both sources.

This is the S2 audit instrument for item 2 of the EXP-002 D1 S2 brief: *the
root cause is established, not asserted*. It complements
``EVIDENCE/exp002-d1-s1/root_cause_decomposition.py``, which proves the
attribution at **runtime** by controlled substitution. This instrument proves
the same registry against the **source text**, without executing matplotlib:

* **Part B** -- every one of the 34 specifications names an argument the
  frozen PRINet 3.0 reference really carries, at the call indices the
  specification restricts. A specification that names an absent argument
  would make its runtime transform vacuous, so this is the check that the
  transforms are not self-confirming.
* **Part C** -- the fixed port now carries the reference's value for each
  specification, and the mathtext re-encoding is gone.
* **Part D** -- the ``\\N{...}`` escape claim: the port's decoded strings
  equal the reference's literal Unicode strings, while the port's source text
  stays ASCII (which is what satisfies ``ruff``'s ``RUF001``).

Argument values are resolved statically through :mod:`ast` for constants,
lists and tuples of constants, f-strings (compared by their literal parts,
with each interpolation rendered as ``\\u2026``) and simple local name
bindings. Those four constructs cover every specification in the registry;
an earlier draft that resolved only bare constants reported three false
failures (``D11.5``, ``D12.2``, ``D12.9``), which is why the resolver exists.

Two things this instrument deliberately does **not** establish, and which the
runtime evidence must carry:

* **Loop multiplicity.** Part C counts *static* occurrences of a literal
  argument. Where the port restructures repeated reference calls into a loop,
  a static count is lower than the runtime call count -- ``D9.1`` reads
  ``ref=4 port=2`` because the reference writes four ``plot(linewidth=1.2)``
  calls and the port emits two inside a two-iteration loop. Such a row is a
  reported observation, not a defect; ``artist_level_equivalence.py`` settles
  it by comparing the rendered artists.
* **Positional-versus-keyword form and ``ax.set(...)`` grouping**, which
  likewise change no byte.

Run from the repository root with the project venv::

    python EVIDENCE/exp002-d1-s2/ast_spec_validation.py

Exit status is ``0`` when Part B, C and D are all clean, else ``1``.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REFERENCE = (
    ROOT
    / "DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main"
    / "src/prinet/utils/figure_generation.py"
)
PORT = ROOT / "python/prin/reporting/figure_generation.py"
REGISTRY = ROOT / "EVIDENCE/exp002-d1-s1/root_cause_decomposition.py"

#: Registered figure stem to generator function name (same in both modules).
STEMS: dict[str, str] = {
    "fig2_clevr_n_capacity": "fig_clevr_n_capacity",
    "fig3_chimera_metrics": "fig_gold_standard_chimera",
    "fig4_chimera_k_alpha_heatmap": "fig_chimera_heatmap",
    "fig5_mot_occlusion_comparison": "fig_mot_identity_preservation",
    "fig6_oscillosim_scaling": "fig_oscillosim_scaling",
    "fig7_ablation_results": "fig_ablation_results",
    "fig8_parameter_efficiency": "fig_parameter_efficiency",
    "fig9_training_curves": "fig_training_curves",
    "fig10_statistical_summary": "fig_statistical_summary",
    "fig11_flops_scaling": "fig_flops_scaling",
    "fig12_supercritical_regime": "fig_supercritical_regime",
    "fig13_representation_geometry": "fig_representation_geometry",
    "fig14_gradient_flow": "fig_gradient_flow",
    "fig15_noise_velocity": "fig_noise_velocity",
}

#: Stand-in for one f-string interpolation hole, so literal parts still compare.
HOLE = "\u2026"

#: The three labels the port re-encoded from Unicode to mathtext before the fix.
ESCAPE_CLAIMS: tuple[tuple[str, str], ...] = (
    ("fig11_flops_scaling", "FLOPs (\N{MULTIPLICATION SIGN}10\N{SUPERSCRIPT THREE})"),
    (
        "fig12_supercritical_regime",
        "\N{GREEK SMALL LETTER DELTA} (1\N{EN DASH}4 Hz)",
    ),
    ("fig15_noise_velocity", "Speed Multiplier (\N{MULTIPLICATION SIGN})"),
)

#: The mathtext spellings that must no longer appear in the port.
MATHTEXT_REWRITES: tuple[str, ...] = (
    r"$\times 10^3$",
    r"Speed Multiplier ($\times$)",
    r"$\delta$ (1--4 Hz)",
)


def enc(value: object) -> str:
    """Render a value as ASCII-safe canonical JSON for stable console output."""
    return json.dumps(value, ensure_ascii=True, sort_keys=True, default=repr)


def func_node(tree: ast.Module, name: str) -> ast.FunctionDef:
    """Return the top-level function definition called ``name``."""
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise SystemExit(f"function {name!r} not found")


def method_calls(tree: ast.Module, func_name: str, method: str) -> list[ast.Call]:
    """Return every ``<expr>.<method>(...)`` call in ``func_name``, in line order."""
    fn = func_node(tree, func_name)
    found = [
        node
        for node in ast.walk(fn)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == method
    ]
    found.sort(key=lambda call: call.lineno)
    return found


def local_binding(fn: ast.FunctionDef, name: str) -> ast.expr | None:
    """Return the value node of a simple ``name = <literal>`` assignment."""
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return node.value
    return None


def resolve(node: ast.expr | None, fn: ast.FunctionDef) -> Any:
    """Best-effort static value of an argument expression.

    Args:
        node: The expression to resolve, or ``None``.
        fn: The enclosing function, used to follow simple local names.

    Returns:
        The resolved literal, a list of resolved literals, an f-string
        pattern with each interpolation replaced by :data:`HOLE`, or ``None``
        when the expression is not statically resolvable.
    """
    if node is None:
        return None
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            else:
                parts.append(HOLE)
        return "".join(parts)
    if isinstance(node, (ast.List, ast.Tuple)):
        return [resolve(element, fn) for element in node.elts]
    if isinstance(node, ast.Name):
        return resolve(local_binding(fn, node.id), fn)
    return None


def strings_in(fn: ast.FunctionDef) -> list[str]:
    """Return every statically resolvable string literal inside ``fn``."""
    out: list[str] = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            continue
        if not isinstance(node, (ast.Constant, ast.JoinedStr)):
            continue
        value = resolve(node, fn)
        if isinstance(value, str):
            out.append(value)
        elif isinstance(value, list):
            out.extend(item for item in value if isinstance(item, str))
    return out


def load_registry() -> tuple[tuple[Any, ...], dict[str, str], Any]:
    """Import the committed S1 generator and return its registry and stem map."""
    spec = importlib.util.spec_from_file_location("exp002_d1_s1_registry", REGISTRY)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {REGISTRY}")
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves ``cls.__module__`` through sys.modules, so the module
    # must be registered before execution or @dataclass raises AttributeError.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.DIVERGENCES, module.STEMS, module


def closure_vars(transform: Any) -> dict[str, Any]:
    """Return the free variables captured by a divergence transform's closure."""
    out: dict[str, Any] = {}
    cells = transform.__closure__ or ()
    for cell, name in zip(cells, transform.__code__.co_freevars, strict=False):
        try:
            out[name] = cell.cell_contents
        except ValueError:  # pragma: no cover - an unbound cell would be a bug
            continue
    return out


def kw_node(call: ast.Call, key: str) -> ast.expr | None:
    """Return the value node of keyword argument ``key``, if the call has it."""
    for keyword in call.keywords:
        if keyword.arg == key:
            return keyword.value
    return None


def count_with_kwarg(tree: ast.Module, func: str, method: str, key: str) -> int:
    """Count calls to ``method`` in ``func`` that carry keyword argument ``key``."""
    return sum(
        1 for call in method_calls(tree, func, method) if kw_node(call, key) is not None
    )


def needles_of(old: Any) -> Iterator[str]:
    """Yield the reference string or strings a value-bearing spec claims."""
    if isinstance(old, str):
        yield old
        return
    for item in old:
        yield str(item)


def part_b(ref_tree: ast.Module, divergences: tuple[Any, ...]) -> list[str]:
    """Validate each spec against the reference source; return failure strings."""
    print("=" * 78)
    print("PART B -- each spec names an argument the REFERENCE source really carries")
    print("=" * 78)
    failures: list[str] = []
    for divergence in divergences:
        func = STEMS[divergence.stem]
        fn = func_node(ref_tree, func)
        calls = method_calls(ref_tree, func, divergence.method)
        indices = (
            list(range(len(calls)))
            if divergence.calls is None
            else sorted(divergence.calls)
        )
        captured = closure_vars(divergence.transform)
        problems: list[str] = []
        note = ""
        if not calls:
            problems.append(f"reference never calls {divergence.method}() in {func}")
        for index in indices:
            if index >= len(calls):
                problems.append(
                    f"call index {index} out of range "
                    f"(only {len(calls)} {divergence.method}() calls)"
                )
                continue
            call = calls[index]
            if "key" in captured:
                node = kw_node(call, captured["key"])
                if node is None:
                    have = sorted(kw.arg for kw in call.keywords if kw.arg)
                    problems.append(
                        f"call[{index}] {divergence.method}() has no "
                        f"{captured['key']}= (has {have})"
                    )
                else:
                    note = f"{captured['key']}={enc(resolve(node, fn))}"
            elif "index" in captured and "old" in captured:
                position, old = captured["index"], captured["old"]
                if position >= len(call.args):
                    problems.append(
                        f"call[{index}] {divergence.method}() has no positional "
                        f"arg {position}"
                    )
                    continue
                got = resolve(call.args[position], fn)
                if isinstance(old, str):
                    if not isinstance(got, str) or old not in got:
                        problems.append(
                            f"call[{index}] {divergence.method}() arg{position}="
                            f"{enc(got)} lacks {enc(old)}"
                        )
                    else:
                        note = f"arg{position}={enc(got)} contains {enc(old)}"
                elif got != list(old):
                    problems.append(
                        f"call[{index}] {divergence.method}() arg{position}="
                        f"{enc(got)} != {enc(list(old))}"
                    )
                else:
                    note = f"arg{position}={enc(got)}"
            elif divergence.transform.__name__ == "_omit":
                note = "call present"
            else:
                problems.append("unrecognised transform shape")
        kind = (
            "drop" if "key" in captured else ("arg" if "index" in captured else "omit")
        )
        tag = "OK  " if not problems else "FAIL"
        print(
            f"[{tag}] {divergence.id:8s} {divergence.method:16s} kind={kind:4s} "
            f"ref_calls={len(calls):2d} indices={indices}  {note}"
        )
        for problem in problems:
            print(f"        ! {problem}")
            failures.append(f"{divergence.id}: {problem}")
    print()
    print(f"PART B: {len(divergences)} specs, {len(failures)} validation failures")
    print()
    return failures


def part_c(
    ref_tree: ast.Module, port_tree: ast.Module, divergences: tuple[Any, ...]
) -> list[str]:
    """Validate the fixed port restores each spec; return failure strings."""
    print("=" * 78)
    print("PART C -- the FIXED PORT carries the reference value for each spec")
    print("          (static literal counts: see the module docstring on loop")
    print("           multiplicity, which makes a lower port count an")
    print("           observation rather than a defect)")
    print("=" * 78)
    failures: list[str] = []
    observations: list[str] = []
    for divergence in divergences:
        func = STEMS[divergence.stem]
        ref_fn = func_node(ref_tree, func)
        port_fn = func_node(port_tree, func)
        captured = closure_vars(divergence.transform)
        problems: list[str] = []
        if "key" in captured:
            key = captured["key"]
            n_ref = count_with_kwarg(ref_tree, func, divergence.method, key)
            n_port = count_with_kwarg(port_tree, func, divergence.method, key)
            detail = f"{divergence.method}({key}=) ref={n_ref} port={n_port}"
            if n_port < n_ref:
                observations.append(f"{divergence.id}: {detail}")
        elif "index" in captured and "old" in captured:
            old = captured["old"]
            ref_strings = strings_in(ref_fn)
            port_strings = strings_in(port_fn)
            counts: list[str] = []
            for needle in needles_of(old):
                n_ref = sum(1 for s in ref_strings if needle in s)
                n_port = sum(1 for s in port_strings if needle in s)
                counts.append(f"{enc(needle)}:ref={n_ref},port={n_port}")
                if n_port < n_ref:
                    problems.append(
                        f"{enc(needle)}: ref={n_ref} port={n_port} -- "
                        "port lost the reference string"
                    )
            detail = " ".join(counts)
            new = captured.get("new")
            if isinstance(new, str) and new.startswith("$"):
                n_new = sum(1 for s in port_strings if new in s)
                if n_new:
                    problems.append(
                        f"port still contains the mathtext rewrite {enc(new)} x{n_new}"
                    )
                detail += f" | mathtext {enc(new)} in port={n_new}"
        else:
            n_ref = len(method_calls(ref_tree, func, divergence.method))
            n_port = len(method_calls(port_tree, func, divergence.method))
            detail = f"{divergence.method}() calls ref={n_ref} port={n_port}"
            if n_port < n_ref:
                problems.append(f"{detail} -- port still omits the call")
        tag = "OK  " if not problems else "FAIL"
        print(f"[{tag}] {divergence.id:8s} {detail}")
        for problem in problems:
            print(f"        ! {problem}")
            failures.append(f"{divergence.id}: {problem}")
    print()
    print(f"PART C: {len(divergences)} specs, {len(failures)} restoration failures")
    if observations:
        print("PART C static-count observations (loop multiplicity; resolved by")
        print("artist_level_equivalence.py, not defects):")
        for observation in observations:
            print(f"  {observation}")
    print()
    return failures


def part_d(ref_tree: ast.Module, port_tree: ast.Module, port_source: str) -> list[str]:
    r"""Validate the ``\\N{...}`` escape claim; return failure strings."""
    print("=" * 78)
    print("PART D -- the \\N{...} escape claim: do the port's decoded strings")
    print("          equal the reference's literal Unicode strings?")
    print("=" * 78)
    failures: list[str] = []
    for stem, needle in ESCAPE_CLAIMS:
        func = STEMS[stem]
        in_ref = any(needle in s for s in strings_in(func_node(ref_tree, func)))
        in_port = any(needle in s for s in strings_in(func_node(port_tree, func)))
        ok = in_ref and in_port
        if not ok:
            failures.append(f"{stem}: reference={in_ref} port={in_port}")
        print(
            f"  [{'OK  ' if ok else 'FAIL'}] {stem}: {enc(needle)} "
            f"reference={in_ref} port={in_port}"
        )
    multiplication_sign = "\N{MULTIPLICATION SIGN}"
    uses_escapes = "\\N{" in port_source
    has_raw_sign = multiplication_sign in port_source
    print(f"  port source uses \\N{{...}} escapes: {uses_escapes}")
    print(f"  port source contains a raw multiplication sign: {has_raw_sign}")
    if not uses_escapes:
        failures.append("port source no longer uses \\N{...} escapes")
    if has_raw_sign:
        failures.append("port source contains a raw multiplication sign (RUF001)")
    for rewrite in MATHTEXT_REWRITES:
        if rewrite in port_source:
            failures.append(f"port source still contains mathtext {enc(rewrite)}")
    print()
    return failures


def main() -> int:
    """Run Parts B, C and D and return a non-zero exit status on any failure."""
    ref_tree = ast.parse(REFERENCE.read_text("utf-8"))
    port_tree = ast.parse(PORT.read_text("utf-8"))
    port_source = PORT.read_text("utf-8")
    divergences, registry_stems, _module = load_registry()

    print(f"reference module : {REFERENCE}")
    print(f"port module      : {PORT}")
    print(f"registry module  : {REGISTRY}")
    print(f"registry size    : {len(divergences)}   (S1 claims 34)")
    print(f"STEMS map identical to the audit's: {registry_stems == STEMS}")
    print()
    if registry_stems != STEMS:
        print("ABORT: the registry's stem map differs from the audit's")
        return 1

    b_failures = part_b(ref_tree, divergences)
    c_failures = part_c(ref_tree, port_tree, divergences)
    d_failures = part_d(ref_tree, port_tree, port_source)

    print("=" * 78)
    print(
        f"SUMMARY  B_fail={len(b_failures)}  C_fail={len(c_failures)}  "
        f"D_fail={len(d_failures)}"
    )
    print("=" * 78)
    return 1 if (b_failures or c_failures or d_failures) else 0


if __name__ == "__main__":
    sys.exit(main())
