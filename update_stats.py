#!/usr/bin/env python3
"""Main script to update GitHub statistics and generate SVG dashboards."""

import os
import sys
from typing import List, Tuple

from stats.github_fetcher import GitHubDataFetcher
from stats.data_processor import DataProcessor
from stats.readme_updater import ReadmeUpdater
from stats.summary_writer import build_summary, write_summary
from stats.svg_generator import (
    ActivityDashboardGenerator,
    OverviewDashboardGenerator,
    TopReposDashboardGenerator,
    LanguagesDashboardGenerator,
)

# Owner/Repo names for top repository stats breakdown
TOP_REPOS: List[Tuple[str, str]] = [
    ("nahpu", "nahpu"),
    ("hhandika", "segul"),
    ("hhandika", "segui"),
    ("hhandika", "ullar"),
    ("mammaldiversity", "mdd_app"),
]

# Public repositories owned by organizations whose code changes by the user
# count toward the totals alongside the user's own repositories
EXTRA_CODE_REPOS: List[str] = [
    "BioVisionLab/BioCosmos",
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

    processor = DataProcessor()
    streak, peak_day = processor.calculate_calendar_metrics(calendar)

    username = user_data.get("login", "hhandika")
    weekday_counts = processor.weekday_totals(calendar)
    hour_counts = fetcher.fetch_hour_counts(username)
    peak_window = processor.peak_hour_window(hour_counts)
    peak_hours = peak_window[2] if peak_window else "Afternoon (12-16)"

    languages = processor.parse_languages(repos_nodes)
    print("Fetching attributed code additions and deletions...")
    owned = {repo.get("nameWithOwner") for repo in repos_nodes}
    code_repos = repos_nodes + [
        {"nameWithOwner": name} for name in EXTRA_CODE_REPOS if name not in owned
    ]
    code_changes = fetcher.fetch_code_changes(username, code_repos)
    additions = code_changes["totals"]["additions"]
    deletions = code_changes["totals"]["deletions"]
    formatted_code_changes = (
        f"+{processor.format_count(additions)} "
        f"(-{processor.format_count(deletions)})"
    )
    if code_changes["status"] == "partial":
        formatted_code_changes += "*"

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

    overview_data = {
        "total_stars": total_stars,
        "total_contributions": total_contributions,
        "total_repositories": total_repos,
        "total_pull_requests": total_prs,
        "total_reviews": total_reviews,
        "total_issues": total_issues,
        "streak_days": streak,
        "peak_day": peak_day,
        "peak_hours": peak_hours,
        "weekday_contributions": dict(
            zip(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], weekday_counts)
        ),
        "hourly_events_et": hour_counts,
        "contribution_calendar": processor.calendar_days(calendar),
        "code_additions": additions,
        "code_deletions": deletions,
        "formatted_code_changes": formatted_code_changes,
    }
    summary = build_summary(
        username=username,
        overview=overview_data,
        languages=languages,
        top_repos=TOP_REPOS,
        repos_data=top_repos_data,
        code_changes=code_changes,
    )

    os.makedirs("assets", exist_ok=True)

    # Each card is written once per theme as <base>-light.svg and <base>-dark.svg
    card_builders = {
        "assets/overview": lambda theme: OverviewDashboardGenerator(
            total_stars=total_stars,
            total_contributions=total_contributions,
            total_repos=total_repos,
            total_prs=total_prs,
            total_reviews=total_reviews,
            total_issues=total_issues,
            streak=streak,
            code_additions=additions,
            code_deletions=deletions,
            code_changes_partial=code_changes["status"] == "partial",
            theme=theme,
        ),
        "assets/languages": lambda theme: LanguagesDashboardGenerator(
            languages=languages, theme=theme
        ),
        "assets/activity": lambda theme: ActivityDashboardGenerator(
            weekday_counts=weekday_counts, hour_counts=hour_counts, theme=theme
        ),
        "assets/top_repos": lambda theme: TopReposDashboardGenerator(
            top_repos=TOP_REPOS, repos_data=top_repos_data, theme=theme
        ),
    }
    for base_path, build in card_builders.items():
        for theme in ("light", "dark"):
            path = f"{base_path}-{theme}.svg"
            with open(path, "w", encoding="utf-8") as f:
                f.write(build(theme).generate())
            print(f"Generated {path}")

    summary_path = "data/stats.json"
    write_summary(summary, summary_path)
    print(f"Generated {summary_path}")

    ReadmeUpdater.update(
        [
            [
                ("assets/overview", "GitHub Stats", "49%"),
                ("assets/languages", "Top Languages", "49%"),
            ],
            [("assets/activity", "Activity Rhythm", "98%")],
            [("assets/top_repos", "Selected Repositories", "98%")],
        ],
        code_changes_partial=code_changes["status"] == "partial",
        summary_path=summary_path,
        total_repos=code_changes["repositories_total"],
        counted_repos=code_changes["repositories_counted"],
    )


if __name__ == "__main__":
    main()
