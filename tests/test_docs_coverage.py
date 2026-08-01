"""DOCS.md's coverage guard (root DOCS.md, "Tiers — Which File Gets Which Docs").

Every source file gets the docs its TIER requires:

    Trivial      -> no __about/, no __flow/ (one line in the folder's
                    ___folder.md instead)
    Standard     -> __about/{name}.md only
    Algorithmic  -> __about/{name}.md AND __flow/{name}.md -- and the flow doc
                    must have EARNED its place (root DOCS.md, owner decision
                    2026-08-01): a Standard-tier file caught with an unearned
                    __flow/ doc fails here too
    tests/       -> NO per-file docs at all, ever -- only the folder's own
                    ___tests.md

This file is the project's single source of truth for every source file's
tier assignment (root MIGRATE-DOCS.md: "the project's test_docs_coverage.py
encodes the tier assignment ... changing a file's tier means updating THIS
test in the same commit").

Run: python -m pytest tests/test_docs_coverage.py
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TRIVIAL = "trivial"
STANDARD = "standard"
ALGORITHMIC = "algorithmic"

# ═══════════════════════════ TIER ASSIGNMENTS ═══════════════════════════

TIERS: dict[str, str] = {
    # -- root: flat, no package -- README.md plays the ___folder.md role ----
    "main.py": TRIVIAL,

    # -- demoapp/ -------------------------------------------------------------
    "demoapp/__init__.py": TRIVIAL,
    "demoapp/flow_layout.py": ALGORITHMIC,
    "demoapp/parts_panel.py": ALGORITHMIC,
    "demoapp/model_panel.py": STANDARD,
    "demoapp/theme.py": STANDARD,
    "demoapp/window.py": ALGORITHMIC,

    # -- preview3d/ -------------------------------------------------------------
    "preview3d/__init__.py": TRIVIAL,
    "preview3d/resources.py": STANDARD,
    "preview3d/vectors.py": STANDARD,
    "preview3d/jsmath.py": STANDARD,
    "preview3d/directions.py": ALGORITHMIC,
    "preview3d/axis_colors.py": ALGORITHMIC,
    "preview3d/orientations.py": ALGORITHMIC,
    "preview3d/model.py": STANDARD,
    "preview3d/model_scene.py": STANDARD,
    "preview3d/cube_model.py": ALGORITHMIC,
    "preview3d/switcher.py": STANDARD,
    "preview3d/cinematics.py": ALGORITHMIC,
    "preview3d/widget.py": STANDARD,

    # -- preview3d/light/ ---------------------------------------------------------
    "preview3d/light/__init__.py": TRIVIAL,
    "preview3d/light/scene.py": STANDARD,
    "preview3d/light/model_view.py": STANDARD,
    "preview3d/light/view.py": STANDARD,
    "preview3d/light/primitives.py": ALGORITHMIC,
    "preview3d/light/camera.py": ALGORITHMIC,
    "preview3d/light/animation.py": ALGORITHMIC,
    "preview3d/light/renderer.py": ALGORITHMIC,

    # -- src/ -------------------------------------------------------------------
    "src/index.js": TRIVIAL,
    "src/views.js": TRIVIAL,
    "src/viewer.js": ALGORITHMIC,
    "src/animation.js": ALGORITHMIC,
    "src/primitives.js": ALGORITHMIC,
    "src/parts.js": STANDARD,
    "src/directions.js": ALGORITHMIC,
    "src/axiscolors.js": ALGORITHMIC,
    "src/orientations.js": ALGORITHMIC,
    "src/model.js": ALGORITHMIC,
    "src/modelscene.js": STANDARD,
    "src/cubemodel.js": STANDARD,
    "src/switcher.js": STANDARD,
    "src/cinematics.js": ALGORITHMIC,
    "src/modelview.js": STANDARD,
    "src/grid.js": STANDARD,
    "src/keyboard.js": STANDARD,
    "src/labels.js": STANDARD,
}

# tests/ files use the dedicated "tests" tier: NO per-file docs, ever -- only
# the folder's ___tests.md (root DOCS.md Tiers table: "tests/ | test modules |
# ___tests.md folder doc only"). They are deliberately absent from TIERS above
# and exempted by directory prefix in test_every_source_file_is_accounted_for.
TEST_TIER_DIR = "tests"

SUFFIXES = (".py", ".js")
EXCLUDED_DIR_NAMES = {".venv", "venv", "node_modules", "__pycache__", ".git", "dist", ".claude", "UV"}
GENERATED_FILES = {"preview3d.min.js"}  # web/preview3d.min.js -- esbuild output, not authored source


def _doc_dir(source_path: Path) -> Path:
    return source_path.parent


def _about_path(source_path: Path) -> Path:
    return _doc_dir(source_path) / "__about" / (source_path.stem + ".md")


def _flow_path(source_path: Path) -> Path:
    return _doc_dir(source_path) / "__flow" / (source_path.stem + ".md")


def _all_source_files():
    for path in PROJECT_ROOT.rglob("*"):
        if path.suffix not in SUFFIXES or not path.is_file():
            continue
        if path.name in GENERATED_FILES:
            continue
        if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
            continue
        yield path


@pytest.mark.parametrize("rel, tier", sorted(TIERS.items()))
def test_file_has_the_docs_its_tier_requires(rel, tier):
    path = PROJECT_ROOT / rel
    assert path.exists(), f"TIERS lists a file that no longer exists: {rel}"
    about = _about_path(path)
    flow = _flow_path(path)

    if tier == TRIVIAL:
        assert not about.exists(), f"{rel} is Trivial tier but has an __about/ doc: {about}"
        assert not flow.exists(), f"{rel} is Trivial tier but has a __flow/ doc: {flow}"
    elif tier == STANDARD:
        assert about.exists(), f"{rel} is Standard tier and needs {about}"
        assert not flow.exists(), (
            f"{rel} is Standard tier but has a __flow/ doc ({flow}) -- root DOCS.md: "
            "the flow doc must EARN its place, downgrade the tier or delete the doc"
        )
    elif tier == ALGORITHMIC:
        assert about.exists(), f"{rel} is Algorithmic tier and needs {about}"
        assert flow.exists(), f"{rel} is Algorithmic tier and needs {flow}"
    else:
        raise AssertionError(f"unknown tier {tier!r} for {rel}")


def test_every_source_file_is_accounted_for():
    """No file falls through the cracks: every .py/.js file outside tests/ is
    in TIERS, and every tests/ file is exempt via its own dedicated tier."""
    missing = []
    for path in _all_source_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        if rel.startswith(TEST_TIER_DIR + "/"):
            continue
        if rel not in TIERS:
            missing.append(rel)
    assert not missing, (
        "Source files with no tier assignment in TIERS -- classify them per "
        "root DOCS.md's Tiers table and add an entry: " + ", ".join(sorted(missing))
    )


def test_no_stale_tier_entries():
    """A TIERS entry for a file that no longer exists (renamed/deleted) is
    exactly the drift the Living Docs Rule exists to prevent."""
    stale = [rel for rel in TIERS if not (PROJECT_ROOT / rel).exists()]
    assert not stale, f"TIERS lists files that no longer exist: {stale}"


def test_tests_folder_has_its_folder_doc_and_no_per_file_docs():
    tests_dir = PROJECT_ROOT / "tests"
    assert (tests_dir / "___tests.md").exists()
    # The "tests" tier forbids per-file docs entirely -- no stray __about/__flow.
    assert not (tests_dir / "__about").exists()
    assert not (tests_dir / "__flow").exists()


def test_no_orphaned_about_or_flow_doc():
    """An __about/ or __flow/ doc whose source file no longer exists (renamed,
    deleted, tier downgraded) structurally CANNOT be true once its subject is
    gone -- exactly the drift the Living Docs Rule exists to prevent."""
    orphans = []
    for about_dir in PROJECT_ROOT.rglob("__about"):
        if any(part in EXCLUDED_DIR_NAMES for part in about_dir.parts):
            continue
        source_dir = about_dir.parent
        for doc in about_dir.glob("*.md"):
            if not any((source_dir / (doc.stem + suffix)).exists() for suffix in SUFFIXES):
                orphans.append(str(doc.relative_to(PROJECT_ROOT)))
    for flow_dir in PROJECT_ROOT.rglob("__flow"):
        if any(part in EXCLUDED_DIR_NAMES for part in flow_dir.parts):
            continue
        source_dir = flow_dir.parent
        for doc in flow_dir.glob("*.md"):
            if not any((source_dir / (doc.stem + suffix)).exists() for suffix in SUFFIXES):
                orphans.append(str(doc.relative_to(PROJECT_ROOT)))
    assert not orphans, f"Orphaned docs (source file gone) -- delete: {orphans}"


def test_the_guard_is_actually_looking_at_this_project():
    assert len(TIERS) > 30, len(TIERS)
    seen_suffixes = {Path(rel).suffix for rel in TIERS}
    assert seen_suffixes == {".py", ".js"}, seen_suffixes
