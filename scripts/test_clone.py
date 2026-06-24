"""Simple script to verify repository cloning works."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.services.clone_service import CloneError, CloneService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

TEST_REPO_URL = "https://github.com/octocat/Hello-World"


def main() -> int:
    settings = get_settings()
    print(f"REPOS_DIR: {settings.repos_dir}")

    service = CloneService(settings)

    try:
        result = service.clone(TEST_REPO_URL)
    except CloneError as exc:
        print(f"Clone failed: {exc}")
        return 1

    print(f"Repository:  {result.repository_name}")
    print(f"Local path:  {result.local_path}")
    print(f"Duplicate:   {result.is_duplicate}")
    print(f"Message:     {result.message}")

    if not result.local_path.exists():
        print("Error: local path does not exist.")
        return 1

    if not (result.local_path / ".git").exists():
        print("Error: .git directory missing.")
        return 1

    duplicate_result = service.clone(TEST_REPO_URL)
    if not duplicate_result.is_duplicate:
        print("Error: expected duplicate detection on second clone.")
        return 1

    print("Duplicate detection OK.")
    print("Clone test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
