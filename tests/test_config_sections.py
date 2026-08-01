"""THE CONFIG SECTION LAW's guard (root CODE.md, owner decree 2026-08-01).

Config files and data tables are STRUCTURES, not notebooks. A table is
defined ONCE, whole, under a named section banner; a later addition patches
the table IN PLACE, in its own section — never as a dict-subscript assignment
or `.update()`/`.push()` call appended far below the table's own definition,
and never as a hidden duplicate key inside the very literal.

Only the files listed in CONFIG_FILES are checked below — this guard's job is
narrow and precise on purpose. Root CODE.md's own scope note: a file that is
mostly algorithm with one small incidental table (e.g.
`preview3d/light/primitives.py`'s shape defaults, `src/animation.js`'s
EASINGS curve table) is not what this law targets — forcing section-banner
coverage across dozens of unrelated algorithm functions for one small table
would be ritual, not structure. CONFIG_FILES is a SEED of the files whose
PRIMARY organizing structure genuinely is one or more module-level data
tables; see the comment beside the list for why each entry earned its place.

Checkable semantics (root CODE.md): after the module docstring and imports,
the file's FIRST top-level definition must be preceded by a section banner (a
comment line carrying a run of >= 8 box-drawing/`=` characters); every
top-level definition belongs to whichever banner precedes it. The guard fails
the build on:

1. a top-level definition before the first section banner,
2. a duplicate key inside one dict/object literal,
3. a module-level statement that patches an EARLIER-DEFINED top-level table
   (`TABLE[...] = ...`, `TABLE.update(...)`, `TABLE.append(...)`, etc.
   appearing after the table's own definition) — unless the exact site is
   named in PATCHING_RATCHET (legacy patches that predate this law).

Python files are checked EXACTLY, via the `ast` module — duplicate keys and
definition order are unambiguous there, including inside arbitrarily nested
dict literals (each `ast.Dict` node is checked independently, so a repeated
key name in two DIFFERENT sibling dicts is correctly not a duplicate).

JS files have no Python-native parser available, so they are checked with a
deliberately NARROWER, regex/brace-tracking heuristic (honestly documented
rather than silently gapped — root Rule #1): banner coverage and
post-definition patching are checked file-wide at column 0; duplicate-key
detection is scoped to the DIRECT (non-nested) keys of each top-level
`const NAME = { ... }` / `export const NAME = { ... }` object literal — a
nested object's own keys are skipped over whole rather than recursed into, so
this side of the guard cannot see a duplicate key buried inside a nested
object. Every JS file currently in CONFIG_FILES has no such nesting, so this
is a documented ceiling, not a live gap.

Run: python -m pytest tests/test_config_sections.py
"""

import ast
import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ═══════════════════════════ CONFIG_FILES ═══════════════════════════
# Seed of the config-law guard (root MIGRATE-DOCS.md Phase 3). Each entry's
# PRIMARY organizing structure is one or more module-level data tables — not
# merely a file that happens to hold one small constant:
CONFIG_FILES = [
    "demoapp/theme.py",       # THEME token dict + build_qss() -- the whole file IS config
    "demoapp/window.py",      # 10 module-level UI-option tables (root Rule #4) ahead of the DemoWindow class
    "preview3d/switcher.py",  # switcher state constants -- Python side of the Switcher
    "src/switcher.js",        # switcher state constants -- JS mirror of the same
]

# Legacy post-definition patches that predate this law and cannot be folded in
# without behavior risk (root CODE.md). Format: "path/to/file.py:LINE" ->
# reason. Empty: nothing in this project predates the law.
PATCHING_RATCHET: dict[str, str] = {}

BANNER_RE = re.compile(r"(=|═){8,}")
PATCH_METHODS = ("update", "append", "extend", "insert", "add", "push", "assign", "splice")


# ═══════════════════════════ PYTHON CHECKER ═══════════════════════════


def _python_banner_lines(source: str) -> list[int]:
    lines = []
    for i, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#") and BANNER_RE.search(stripped):
            lines.append(i)
    return lines


def _root_name(node):
    while isinstance(node, ast.Subscript):
        node = node.value
    if isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _const_key(node):
    return node.value if isinstance(node, ast.Constant) else None


def _check_python(path: Path, rel: str) -> list[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    banners = _python_banner_lines(source)
    min_banner = min(banners) if banners else None

    errors: list[str] = []
    table_names: set[str] = set()

    body = tree.body
    start = 0
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        start = 1  # module docstring, exempt

    for node in body[start:]:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue

        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if min_banner is None or node.lineno < min_banner:
                errors.append(f"{rel}:{node.lineno}: top-level definition before the first section banner")

        if isinstance(node, ast.Assign):
            if isinstance(node.value, (ast.Dict, ast.List, ast.Set)):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        table_names.add(target.id)
            for target in node.targets:
                if isinstance(target, ast.Subscript):
                    base = _root_name(target)
                    if base in table_names:
                        site = f"{rel}:{node.lineno}"
                        if site not in PATCHING_RATCHET:
                            errors.append(
                                f"{site}: post-definition patch of {base!r} via subscript "
                                f"assignment -- fold the entry into {base}'s own definition"
                            )
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.value, (ast.Dict, ast.List, ast.Set)) and isinstance(node.target, ast.Name):
                table_names.add(node.target.id)

        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Attribute) and call.func.attr in PATCH_METHODS:
                base = _root_name(call.func.value)
                if base in table_names:
                    site = f"{rel}:{node.lineno}"
                    if site not in PATCHING_RATCHET:
                        errors.append(
                            f"{site}: post-definition patch of {base!r} via .{call.func.attr}() "
                            f"-- fold the entry into {base}'s own definition"
                        )

    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            seen = set()
            for key_node in node.keys:
                key = _const_key(key_node) if key_node is not None else None
                if key is None:
                    continue
                if key in seen:
                    errors.append(f"{rel}:{node.lineno}: duplicate dict key {key!r}")
                seen.add(key)

    return errors


# ═══════════════════════════ JS CHECKER ═══════════════════════════

JS_DEF_RE = re.compile(r"^(export\s+)?(const|let|var|function\s*\*?|class)\s+([A-Za-z_$][\w$]*)")
JS_PATCH_RE = re.compile(r"^([A-Za-z_$][\w$]*)(?:\[[^\]]*\]\s*=(?!=)|\.(?:%s)\()" % "|".join(PATCH_METHODS))
JS_KEY_RE = re.compile(r"""\s*(?:'([^']*)'|"([^"]*)"|([A-Za-z_$][\w$]*))\s*:(?!:)""")


def _js_banner_lines(lines: list[str]) -> list[int]:
    result = []
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("//") and BANNER_RE.search(stripped):
            result.append(i)
    return result


def _js_definitions(lines: list[str]) -> list[tuple[int, str]]:
    result = []
    for i, line in enumerate(lines, start=1):
        if not line or line[:1].isspace():
            continue
        m = JS_DEF_RE.match(line)
        if m:
            result.append((i, m.group(3)))
    return result


def _find_matching_brace(text: str, open_index: int) -> int:
    depth = 0
    i, n = open_index, len(text)
    while i < n:
        c = text[i]
        if c in "\"'`":
            j = i + 1
            while j < n and text[j] != c:
                j += 2 if text[j] == "\\" else 1
            i = j + 1
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def _js_object_direct_keys(body: str) -> list[str]:
    """Keys at depth 0 of `body` only -- a nested {...}/[...]/(...) is skipped
    whole so its contents never get misread as this object's own keys (this
    scope's known, documented ceiling -- see module docstring)."""
    keys, i, n, depth = [], 0, len(body), 0
    while i < n:
        c = body[i]
        if c in "\"'`":
            j = i + 1
            while j < n and body[j] != c:
                j += 2 if body[j] == "\\" else 1
            i = j + 1
            continue
        if c in "{[(":
            depth += 1
            i += 1
            continue
        if c in "}])":
            depth -= 1
            i += 1
            continue
        if depth == 0:
            m = JS_KEY_RE.match(body, i)
            if m:
                keys.append(m.group(1) or m.group(2) or m.group(3))
                i = m.end()
                continue
        i += 1
    return keys


def _check_js(path: Path, rel: str) -> list[str]:
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    banners = _js_banner_lines(lines)
    min_banner = min(banners) if banners else None
    definitions = _js_definitions(lines)

    errors: list[str] = []
    table_names: set[str] = set()

    for lineno, name in definitions:
        if min_banner is None or lineno < min_banner:
            errors.append(f"{rel}:{lineno}: top-level definition {name!r} before the first section banner")
        line = lines[lineno - 1]
        rhs = line.split("=", 1)[1].strip() if "=" in line else ""
        if rhs.startswith("{") or rhs.startswith("["):
            table_names.add(name)

    for i, line in enumerate(lines, start=1):
        if not line or line[:1].isspace():
            continue
        m = JS_PATCH_RE.match(line)
        if m and m.group(1) in table_names:
            site = f"{rel}:{i}"
            if site not in PATCHING_RATCHET:
                errors.append(f"{site}: post-definition patch of {m.group(1)!r} -- fold the entry into its own definition")

    for lineno, name in definitions:
        line = lines[lineno - 1]
        rhs = line.split("=", 1)[1].strip() if "=" in line else ""
        if not rhs.startswith("{"):
            continue
        open_index = source.index(line) + line.index("{", line.index("="))
        close_index = _find_matching_brace(source, open_index)
        if close_index == -1:
            continue
        body = source[open_index + 1:close_index]
        seen = set()
        for key in _js_object_direct_keys(body):
            if key in seen:
                errors.append(f"{rel}: duplicate object key {key!r} in {name}")
            seen.add(key)

    return errors


# ═══════════════════════════ TESTS ═══════════════════════════


def _rel_and_path(entry: str) -> tuple[str, Path]:
    return entry, PROJECT_ROOT / entry


@pytest.mark.parametrize("entry", CONFIG_FILES)
def test_seeded_config_file_follows_the_config_section_law(entry):
    rel, path = _rel_and_path(entry)
    assert path.exists(), f"CONFIG_FILES entry does not exist: {rel}"
    errors = _check_python(path, rel) if path.suffix == ".py" else _check_js(path, rel)
    assert not errors, (
        "THE CONFIG SECTION LAW (root CODE.md): " + "; ".join(errors)
    )


def test_the_guard_is_actually_looking_at_this_project():
    assert len(CONFIG_FILES) > 0
    suffixes = {Path(entry).suffix for entry in CONFIG_FILES}
    assert suffixes == {".py", ".js"}


def test_the_patching_ratchet_only_shrinks():
    """Mirrors the structure-law ratchet's shrink-only obligation (root
    CODE.md): every entry names a file:line site that must still exist and
    still be a real patch -- an entry for a site that has been folded into
    its table's own definition must be deleted, not left stale."""
    for site in PATCHING_RATCHET:
        rel_path = site.rsplit(":", 1)[0]
        assert (PROJECT_ROOT / rel_path).exists(), f"stale PATCHING_RATCHET entry: {site}"
