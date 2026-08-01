"""Fast guard runner for Claude Code hooks (root CODE.md, Enforcement).

Runs the project's guard tests via `pytest.main`, prints a failure summary to
stderr, and exits **2** on failure — exit 2 is what makes a PostToolUse/Stop
hook BLOCKING. Stays fast (well under ~2 s) and deterministic: guards only,
never the full component test suite (`tests/test_*_parity.py` etc. take over
a minute and belong to `python -m pytest tests/`, not here).

Usage:
    python tests/run_guards.py           # all four guards (Stop hook)
    python tests/run_guards.py --fast    # structure law + config sections only (PostToolUse hook)

When Claude Code invokes this as a PostToolUse hook, the tool-call JSON
arrives on stdin: `{"tool_input": {"file_path": "..."}, ...}`. In `--fast`
mode, a call for a file that is NOT `.py`/`.js` exits 0 immediately, before
`pytest` is even imported — a docs-only session must not pay the guard cost
on every single markdown edit.
"""

import json
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent

ALL_GUARDS = [
    "test_structure_law.py",
    "test_config_sections.py",
    "test_docs_coverage.py",
    "test_doc_links.py",
]
FAST_GUARDS = ["test_structure_law.py", "test_config_sections.py"]

SOURCE_SUFFIXES = (".py", ".js")


def _hook_payload() -> dict | None:
    """The PostToolUse JSON on stdin, or None if there is nothing to read
    (interactive terminal, empty pipe, or not valid JSON)."""
    if sys.stdin.isatty():
        return None
    try:
        raw = sys.stdin.read()
    except Exception:
        return None
    if not raw.strip():
        return None
    try:
        return json.loads(raw)
    except ValueError:
        return None


def _fast_exit_for_non_source() -> bool:
    """True when this is a PostToolUse call for a file that is not .py/.js —
    the FAST guards (structure law, config sections) have nothing to check."""
    payload = _hook_payload()
    if payload is None:
        return False
    file_path = payload.get("tool_input", {}).get("file_path")
    if not file_path:
        return False
    return Path(file_path).suffix not in SOURCE_SUFFIXES


def main() -> int:
    fast = "--fast" in sys.argv[1:]
    if fast and _fast_exit_for_non_source():
        return 0

    import pytest

    guards = FAST_GUARDS if fast else ALL_GUARDS
    args = [str(TESTS_DIR / name) for name in guards] + ["-q"]
    result = pytest.main(args)
    if result != 0:
        print(
            "\nGUARD FAILURE — THE STRUCTURE LAW / CONFIG SECTION LAW / "
            "DOCS.md enforcement (root CODE.md) is blocking until this is "
            "fixed. See the pytest output above for which guard and why.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
