"""Repository cloning service using GitPython."""

from __future__ import annotations

import logging
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from git import GitCommandError, InvalidGitRepositoryError, Repo

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

GITHUB_URL_PATTERN = re.compile(
    r"^(?:https?://)?(?:www\.)?github\.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(?:\.git)?/?$"
)
GITHUB_SHORTHAND_PATTERN = re.compile(r"^(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)$")


class CloneError(Exception):
    """Raised when a repository cannot be cloned."""


@dataclass(frozen=True)
class CloneResult:
    """Outcome of a clone operation."""

    repository_name: str
    local_path: Path
    is_duplicate: bool
    message: str


class CloneService:
    """Clone GitHub repositories into a local directory."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self.repos_dir = self._settings.repos_dir
        self.repos_dir.mkdir(parents=True, exist_ok=True)

    def clone(self, github_url: str) -> CloneResult:
        """
        Clone a GitHub repository or return the existing local copy.

        Args:
            github_url: HTTPS GitHub URL or owner/repo shorthand.

        Returns:
            CloneResult with repository name, local path, and duplicate flag.

        Raises:
            CloneError: If the URL is invalid or cloning fails.
        """
        owner, repo_name = self._parse_github_url(github_url)
        repository_name = f"{owner}/{repo_name}"
        clone_url = f"https://github.com/{repository_name}.git"
        local_path = self.repos_dir / f"{owner}_{repo_name}"

        if self._is_duplicate(local_path):
            message = f"Repository '{repository_name}' already exists locally."
            logger.info("%s Path: %s", message, local_path)
            return CloneResult(
                repository_name=repository_name,
                local_path=local_path,
                is_duplicate=True,
                message=message,
            )

        logger.info("Cloning '%s' into %s", repository_name, local_path)
        try:
            Repo.clone_from(clone_url, local_path, depth=1)
        except GitCommandError as exc:
            if local_path.exists():
                shutil.rmtree(local_path, ignore_errors=True)
            logger.error("Failed to clone '%s': %s", repository_name, exc)
            raise CloneError(
                f"Failed to clone '{repository_name}'. "
                "Verify the URL is public and accessible."
            ) from exc

        if not self._is_duplicate(local_path):
            logger.error("Clone finished but repository is invalid at %s", local_path)
            raise CloneError(
                f"Clone of '{repository_name}' completed but the local repository is invalid."
            )

        message = f"Successfully cloned '{repository_name}'."
        logger.info("%s Path: %s", message, local_path)
        return CloneResult(
            repository_name=repository_name,
            local_path=local_path,
            is_duplicate=False,
            message=message,
        )

    def _parse_github_url(self, github_url: str) -> tuple[str, str]:
        """Extract owner and repository name from a GitHub URL or shorthand."""
        normalized = github_url.strip().rstrip("/")

        shorthand_match = GITHUB_SHORTHAND_PATTERN.match(normalized)
        if shorthand_match:
            return shorthand_match.group("owner"), shorthand_match.group("repo")

        if "://" not in normalized:
            normalized = f"https://{normalized}"

        parsed = urlparse(normalized)
        if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
            raise CloneError(
                f"Unsupported repository URL: '{github_url}'. "
                "Only github.com repositories are supported."
            )

        path_match = GITHUB_URL_PATTERN.match(normalized)
        if not path_match:
            raise CloneError(
                f"Invalid GitHub repository URL: '{github_url}'. "
                "Expected format: https://github.com/owner/repo"
            )

        return path_match.group("owner"), path_match.group("repo")

    def _is_duplicate(self, local_path: Path) -> bool:
        """Return True when a valid git repository already exists at local_path."""
        if not local_path.exists():
            return False

        try:
            Repo(local_path)
            return True
        except InvalidGitRepositoryError:
            logger.warning("Removing invalid directory at %s", local_path)
            shutil.rmtree(local_path, ignore_errors=True)
            return False
