"""DOCS.md's navigation-chain guard.

Root DOCS.md ("Navigation Chain & Link Formatting"): from the project's
README.md you must be able to reach EVERY project `.md` file by following
links (`README.md -> ___module.md -> __about/*, __flow/*`), and no relative
link may point at a file that does not exist. An orphaned or broken-linked
doc is a build failure here, exactly like a missing test would be.

Two things stay outside this guard's reach, both by DOCS.md's own design:

- Links into `UV/` (the owner's gitignored inbox) -- the target set is
  volatile and the folder is not walked at all.
- Monorepo-root doc references (e.g. `rules/CODE.md`) -- DOCS.md requires
  those to be written as plain backtick text, never as markdown links,
  precisely because a project-level guard cannot assert targets outside the
  project. Any relative link that resolves outside PROJECT_ROOT is therefore
  skipped rather than asserted.

Run: python -m pytest tests/test_doc_links.py
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
README = PROJECT_ROOT / "README.md"

# Directories whose .md files are neither walked nor required (DOCS.md
# "Navigation Chain" -- excluded directories).
EXCLUDED_DIR_NAMES = {
    ".git", ".claude", "UV", "node_modules", "__pycache__", ".pytest_cache",
    "dist", "build",
}

# Data `.md` files that are content, not documentation -- exempt from the
# reachability requirement (DOCS.md "Tiers": "fixtures, sample sheets sit in
# the test's EXEMPT list"). Empty here: this project has no data .md files.
EXEMPT_FROM_REACHABILITY: set[str] = set()

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _project_md_files():
    for path in PROJECT_ROOT.rglob("*.md"):
        rel_parts = path.relative_to(PROJECT_ROOT).parts
        if any(part in EXCLUDED_DIR_NAMES for part in rel_parts):
            continue
        yield path


def _links_in(md_path: Path):
    text = md_path.read_text(encoding="utf-8")
    for raw in LINK_RE.findall(text):
        target = raw.strip()
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if target.startswith("#"):
            continue  # in-page anchor, not a file link
        path_part = target.split("#", 1)[0]  # drop a `file.md#anchor` suffix
        if not path_part:
            continue
        yield path_part


def _resolve(from_file: Path, rel: str) -> Path:
    return (from_file.parent / rel).resolve()


def test_every_project_doc_is_reachable_from_readme():
    """BFS the .md link graph starting at README.md; every walked .md must
    be found, or it is an orphan the navigation chain does not cover."""
    all_docs = {p.resolve() for p in _project_md_files()}
    seen: set[Path] = set()
    frontier = [README.resolve()]
    while frontier:
        current = frontier.pop()
        if current in seen or current not in all_docs:
            continue
        seen.add(current)
        for rel in _links_in(current):
            if not rel.endswith(".md"):
                continue
            target = _resolve(current, rel)
            if target in all_docs and target not in seen:
                frontier.append(target)

    unreachable = sorted(
        p.relative_to(PROJECT_ROOT).as_posix()
        for p in (all_docs - seen)
        if p.relative_to(PROJECT_ROOT).as_posix() not in EXEMPT_FROM_REACHABILITY
    )
    assert not unreachable, (
        "DOCS.md navigation chain broken -- unreachable from README.md: "
        + ", ".join(unreachable)
    )


def test_no_relative_link_is_broken():
    """Every relative link inside a project .md must resolve to a real file
    (a doc, or a script via the explicit "(script)" link). Links that
    resolve outside PROJECT_ROOT are monorepo-root references written as
    plain text per DOCS.md and never reach here as links in the first
    place -- if one DOES appear as a markdown link, it is out of this
    guard's jurisdiction (a project guard cannot assert targets outside the
    project), so it is skipped rather than asserted."""
    broken = []
    for md in _project_md_files():
        for rel in _links_in(md):
            target = _resolve(md, rel)
            try:
                target.relative_to(PROJECT_ROOT)
            except ValueError:
                continue  # escapes the project: not this guard's concern
            if not target.exists():
                broken.append(f"{md.relative_to(PROJECT_ROOT).as_posix()} -> {rel}")
    assert not broken, "Broken relative links: " + ", ".join(broken)


def test_the_guard_is_actually_looking_at_this_project():
    """A guard that walks zero docs passes forever."""
    all_docs = list(_project_md_files())
    assert len(all_docs) > 10, len(all_docs)
    assert README.exists()
