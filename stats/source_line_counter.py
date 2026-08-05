"""Counts source lines in public repositories with cloc."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from stats.data_processor import EXCLUDED_LANGUAGES


class SourceLineCounter:
    """Clone repositories and aggregate exact code-line statistics."""

    def __init__(self, executable: str = "cloc", timeout: int = 180) -> None:
        self.executable = executable
        self.timeout = timeout

    def count_repositories(
        self, repositories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Count Git-tracked source files, retaining per-repository failures."""
        if shutil.which(self.executable) is None:
            raise RuntimeError(
                f"Required source line counter '{self.executable}' was not found."
            )

        version_result = subprocess.run(
            [self.executable, "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )
        version = version_result.stdout.strip()
        repository_results = []
        failures = []
        totals = {"files": 0, "blank": 0, "comment": 0, "code": 0}
        languages: Dict[str, Dict[str, int]] = {}

        with tempfile.TemporaryDirectory(prefix="github-loc-") as temp_dir:
            for index, repository in enumerate(repositories):
                name_with_owner = repository.get("nameWithOwner") or repository.get(
                    "name", f"repository-{index + 1}"
                )
                url = repository.get("url")
                checkout = Path(temp_dir) / f"repository-{index + 1}"
                if not url:
                    failures.append(
                        {
                            "name_with_owner": name_with_owner,
                            "stage": "clone",
                            "error": "Repository URL is missing.",
                        }
                    )
                    continue

                try:
                    subprocess.run(
                        [
                            "git",
                            "clone",
                            "--depth",
                            "1",
                            "--single-branch",
                            "--quiet",
                            url,
                            str(checkout),
                        ],
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=self.timeout,
                    )
                except (
                    subprocess.CalledProcessError,
                    subprocess.TimeoutExpired,
                    OSError,
                ) as error:
                    failures.append(self._failure(name_with_owner, "clone", error))
                    continue

                try:
                    cloc_result = subprocess.run(
                        [self.executable, "--json", "--quiet", "--vcs=git"],
                        cwd=checkout,
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=self.timeout,
                    )
                    parsed = self._parse_cloc_output(cloc_result.stdout)
                except (
                    subprocess.CalledProcessError,
                    subprocess.TimeoutExpired,
                    OSError,
                    ValueError,
                    json.JSONDecodeError,
                ) as error:
                    failures.append(self._failure(name_with_owner, "count", error))
                    continue

                repository_result = {
                    "name_with_owner": name_with_owner,
                    "url": url,
                    **parsed,
                }
                repository_results.append(repository_result)
                self._merge_counts(totals, parsed["totals"])
                for language, counts in parsed["languages"].items():
                    aggregate = languages.setdefault(
                        language, {"files": 0, "blank": 0, "comment": 0, "code": 0}
                    )
                    self._merge_counts(aggregate, counts)

        return {
            "status": "partial" if failures else "complete",
            "counter": {"name": "cloc", "version": version},
            "repositories_total": len(repositories),
            "repositories_counted": len(repository_results),
            "repositories_failed": len(failures),
            "totals": totals,
            "languages": languages,
            "repositories": repository_results,
            "failures": failures,
        }

    @staticmethod
    def _parse_cloc_output(output: str) -> Dict[str, Any]:
        raw = json.loads(output)
        languages = {}
        totals = {"files": 0, "blank": 0, "comment": 0, "code": 0}
        for language, raw_counts in raw.items():
            if language in {"header", "SUM"} or language.lower() in EXCLUDED_LANGUAGES:
                continue
            counts = {
                "files": int(raw_counts.get("nFiles", 0)),
                "blank": int(raw_counts.get("blank", 0)),
                "comment": int(raw_counts.get("comment", 0)),
                "code": int(raw_counts.get("code", 0)),
            }
            languages[language] = counts
            SourceLineCounter._merge_counts(totals, counts)
        return {"totals": totals, "languages": languages}

    @staticmethod
    def _merge_counts(target: Dict[str, int], source: Dict[str, int]) -> None:
        for key in ("files", "blank", "comment", "code"):
            target[key] += source[key]

    @staticmethod
    def _failure(name_with_owner: str, stage: str, error: Exception) -> Dict[str, str]:
        detail = getattr(error, "stderr", None) or str(error)
        return {
            "name_with_owner": name_with_owner,
            "stage": stage,
            "error": str(detail).strip()[:500],
        }
