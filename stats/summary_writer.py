"""Builds and writes the generated GitHub statistics summary."""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


def build_summary(
    username: str,
    overview: Dict[str, Any],
    languages: Dict[str, Dict[str, Any]],
    top_repos: List[Tuple[str, str]],
    repos_data: List[Optional[Dict[str, Any]]],
    line_count: Dict[str, Any],
) -> Dict[str, Any]:
    """Create the versioned public data representation of generated statistics."""
    total_language_bytes = sum(item.get("size", 0) for item in languages.values())
    language_summary = {}
    for name, item in sorted(
        languages.items(), key=lambda language: language[1].get("size", 0), reverse=True
    ):
        size = item.get("size", 0)
        language_summary[name] = {
            "bytes": size,
            "color": item.get("color"),
            "percentage": round(size / total_language_bytes * 100, 2)
            if total_language_bytes
            else 0.0,
        }

    featured_repositories = []
    for (owner, name), repository in zip(top_repos, repos_data):
        if not repository:
            featured_repositories.append(
                {"name_with_owner": f"{owner}/{name}", "available": False}
            )
            continue
        edges = repository.get("languages", {}).get("edges", [])
        language_bytes = sum(edge.get("size", 0) for edge in edges)
        featured_repositories.append(
            {
                "name_with_owner": f"{owner}/{name}",
                "available": True,
                "description": repository.get("description"),
                "languages": [
                    {
                        "name": edge["node"]["name"],
                        "color": edge["node"].get("color"),
                        "bytes": edge.get("size", 0),
                        "percentage": round(
                            edge.get("size", 0) / language_bytes * 100, 2
                        )
                        if language_bytes
                        else 0.0,
                    }
                    for edge in edges
                ],
            }
        )

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": line_count["status"],
        "profile": {"username": username, "public_only": True},
        "overview": overview,
        "language_statistics": {
            "unit": "bytes",
            "total": total_language_bytes,
            "languages": language_summary,
        },
        "source_line_count": line_count,
        "featured_repositories": featured_repositories,
    }


def write_summary(summary: Dict[str, Any], path: str = "data/stats.json") -> None:
    """Write formatted JSON, creating the root-level data directory as needed."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as summary_file:
        json.dump(summary, summary_file, indent=2, sort_keys=True)
        summary_file.write("\n")
