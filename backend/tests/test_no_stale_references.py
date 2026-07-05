"""Grep invariant test (design review warning #3).

Ensures zero case-insensitive matches for Tortoise/Motor/Postgres artifacts
and dead schema imports across the backend/app/ source tree.
"""

from pathlib import Path

import pytest

BACKEND_APP_DIR = Path(__file__).resolve().parent.parent / "app"

FORBIDDEN_PATTERNS = [
    "tortoise",
    "motor",
    "postgres_",
    "from app.db.schema import",
]


def _collect_py_files():
    """Walk backend/app/ and collect all .py files."""
    return list(BACKEND_APP_DIR.rglob("*.py"))


@pytest.mark.parametrize("pattern", FORBIDDEN_PATTERNS)
def test_no_stale_references(pattern):
    """Assert zero case-insensitive matches for forbidden patterns in backend/app/."""
    py_files = _collect_py_files()
    assert len(py_files) > 0, "No .py files found in backend/app/"

    violations = []
    for filepath in py_files:
        content = filepath.read_text(encoding="utf-8", errors="replace")
        if pattern.lower() in content.lower():
            violations.append(str(filepath.relative_to(BACKEND_APP_DIR.parent.parent)))

    assert not violations, (
        f"Found forbidden pattern '{pattern}' in: {', '.join(violations)}"
    )
