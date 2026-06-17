#!/usr/bin/env python3
"""Main script to update GitHub statistics and generate SVG dashboards."""

import os
import sys
from typing import List, Tuple

from stats.github_fetcher import GitHubDataFetcher
from stats.data_processor import DataProcessor
from stats.readme_updater import ReadmeUpdater
from stats.svg_generator import OverviewDashboardGenerator, TopReposDashboardGenerator

# Owner/Repo names for top repository stats breakdown
TOP_REPOS: List[Tuple[str, str]] = [
    ("nahpu", "nahpu"),
    ("hhandika", "segul"),
    ("hhandika", "segui"),
    ("hhandika", "ullar"),
    ("mammaldiversity", "mdd_app"),
]


def main() -> None:
    """Main function orchestration."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print(
            "Error: GITHUB_TOKEN environment variable not set. Exiting.",
            file=sys.stderr,
        )
        sys.exit(1)

    fetcher = GitHubDataFetcher(token)

    print("Fetching data from GitHub GraphQL API...")
    data = fetcher.fetch_graphql_data()

    user_data = data.get("user", {})
    if not user_data:
        print("Error: Could not retrieve user data.", file=sys.stderr)
        sys.exit(1)

    contributions_collection = user_data.get("contributionsCollection", {})
    calendar = contributions_collection.get("contributionCalendar", {})
    total_contributions = calendar.get("totalContributions", 0)

    total_prs = contributions_collection.get("totalPullRequestContributions", 0)
    total_reviews = contributions_collection.get(
        "totalPullRequestReviewContributions", 0
    )
    total_issues = contributions_collection.get("totalIssueContributions", 0)

    repos_nodes = user_data.get("repositories", {}).get("nodes", [])
    total_repos = len(repos_nodes)
    total_stars = sum(repo.get("stargazerCount", 0) for repo in repos_nodes)
    total_forks = sum(repo.get("forkCount", 0) for repo in repos_nodes)
    cri = total_forks / total_repos if total_repos > 0 else 0.0

    processor = DataProcessor()
    streak, peak_day = processor.calculate_calendar_metrics(calendar)

    username = user_data.get("login", "hhandika")
    peak_hours = fetcher.fetch_peak_hours(username)

    languages = processor.parse_languages(repos_nodes)

    top_repos_data = []
    for owner, name in TOP_REPOS:
        alias = name.replace("-", "_")
        repo_info = data.get(alias)
        if not repo_info:
            for k, v in data.items():
                if (
                    isinstance(v, dict)
                    and v.get("name") == name
                    and v.get("owner", {}).get("login") == owner
                ):
                    repo_info = v
                    break
        top_repos_data.append(repo_info)

    os.makedirs("assets", exist_ok=True)

    overview_generator = OverviewDashboardGenerator(
        total_stars=total_stars,
        total_contributions=total_contributions,
        total_repos=total_repos,
        total_prs=total_prs,
        total_reviews=total_reviews,
        total_issues=total_issues,
        cri=cri,
        streak=streak,
        peak_day=peak_day,
        peak_hours=peak_hours,
        languages=languages,
    )
    overview_svg = overview_generator.generate()

    languages_generator = LanguagesDashboardGenerator(languages=languages)
    languages_svg = languages_generator.generate()

    top_repos_generator = TopReposDashboardGenerator(
        top_repos=TOP_REPOS, repos_data=top_repos_data
    )
    top_repos_svg = top_repos_generator.generate()

    overview_path = "assets/overview.svg"
    languages_path = "assets/languages.svg"
    top_repos_path = "assets/top_repos.svg"

    with open(overview_path, "w", encoding="utf-8") as f:
        f.write(overview_svg)
    print(f"Generated {overview_path}")

    with open(languages_path, "w", encoding="utf-8") as f:
        f.write(languages_svg)
    print(f"Generated {languages_path}")

    with open(top_repos_path, "w", encoding="utf-8") as f:
        f.write(top_repos_svg)
    print(f"Generated {top_repos_path}")

    ReadmeUpdater.update(overview_path, languages_path, top_repos_path)


if __name__ == "__main__":
    main()
