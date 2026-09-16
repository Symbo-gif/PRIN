"""Execute every Python code block in the Sphinx guides (WP037-F4 remediation).

Documentation Standards s1.4/s7 item 4 requires shipped Python examples to be
executable. The Sphinx guides (``getting_started.rst``,
``coupling_topologies.rst``, ``capacity_analysis.rst``) use ``code-block::
python`` directives rather than doctests, so this module extracts each block
and runs the concatenated script per guide in an isolated namespace. A guide
passes if every block completes without raising; output comments (``# 0.3.0``)
are documentation, not assertions.

Blocks that use IPython magics (``%matplotlib inline``) have the magic line
stripped before execution — the test validates the Python, not the display
backend. Blocks marked ``# sphinx-example: skip`` are excluded.
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg", force=True)

ROOT = Path(__file__).resolve().parents[1]
SPHINX = ROOT / "DOCS" / "sphinx"

_GUIDES_WITH_EXAMPLES = (
    "getting_started.rst",
    "coupling_topologies.rst",
    "capacity_analysis.rst",
)

_CODE_BLOCK = re.compile(
    r"^\.\. code-block:: python\s*\n((?:\n|   .+\n)*)",
    re.MULTILINE,
)


def _extract_code_blocks(rst_path: Path) -> list[str]:
    """Return dedented Python source from every ``code-block:: python`` in a guide.

    Args:
        rst_path: Path to the reStructuredText guide.

    Returns:
        List of dedented Python source strings.
    """
    text = rst_path.read_text(encoding="utf-8")
    raw_blocks = _CODE_BLOCK.findall(text)
    blocks: list[str] = []
    for raw in raw_blocks:
        lines = raw.splitlines()
        stripped = []
        for line in lines:
            if line.startswith("   "):
                stripped.append(line[3:])
            elif line.strip() == "":
                stripped.append("")
        source = "\n".join(stripped).strip()
        if source and "sphinx-example: skip" not in source:
            blocks.append(source)
    return blocks


def _prepare_source(rst_path: Path) -> str:
    """Return the concatenated, cleaned source from all blocks in a guide.

    IPython magics are stripped; ``plt.show()`` calls are replaced with
    ``plt.close("all")`` to avoid blocking on the non-interactive Agg backend.

    Args:
        rst_path: Path to the reStructuredText guide.

    Returns:
        Single Python source string for execution.
    """
    blocks = _extract_code_blocks(rst_path)
    cleaned: list[str] = []
    for block in blocks:
        lines = []
        for line in block.splitlines():
            stripped = line.strip()
            if stripped.startswith("%"):
                continue
            if stripped == "plt.show()":
                lines.append("plt.close('all')")
            else:
                lines.append(line)
        cleaned.append("\n".join(lines))
    return "\n\n".join(cleaned)


@pytest.mark.slow
@pytest.mark.parametrize(
    "guide",
    _GUIDES_WITH_EXAMPLES,
)
def test_sphinx_guide_examples_execute(guide: str) -> None:
    """Assert all Python code blocks in a Sphinx guide run without raising.

    Args:
        guide: Source guide filename.
    """
    path = SPHINX / guide
    if not path.is_file():
        pytest.skip(f"{guide} not present")
    source = _prepare_source(path)
    namespace: dict[str, object] = {}
    exec(
        compile(textwrap.dedent(source), f"<sphinx-example:{guide}>", "exec"),
        namespace,
    )
