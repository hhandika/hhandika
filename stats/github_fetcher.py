"""Handles fetching and parsing data from the GitHub API."""

import json
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Dict, Any, List

from stats.data_processor import DataProcessor

GRAPHQL_QUERY = """
query($repositoriesCursor: String) {
  user(login: "hhandika") {
    name
    login
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
            weekday
          }
        }
      }
    }
    repositories(first: 100, after: $repositoriesCursor, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, orderBy: {field: STARGAZERS, direction: DESC}) {
      nodes {
        name
        nameWithOwner
        url
        stargazerCount
        forkCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
              color
            }
          }
        }
      }
      pageInfo {
        endCursor
        hasNextPage
      }
    }
  }
  nahpu: repository(owner: "nahpu", name: "nahpu") {
    ...RepoFields
  }
  segul: repository(owner: "hhandika", name: "segul") {
    ...RepoFields
  }
  segui: repository(owner: "hhandika", name: "segui") {
    ...RepoFields
  }
  ullar: repository(owner: "hhandika", name: "ullar") {
    ...RepoFields
  }
  mdd_app: repository(owner: "mammaldiversity", name: "mdd_app") {
    ...RepoFields
  }
  BioCosmos: repository(owner: "BioVisionLab", name: "BioCosmos") {
    ...RepoFields
  }
}

fragment RepoFields on Repository {
  name
  owner {
    login
  }
  description
  stargazerCount
  pushedAt
  languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
    edges {
      size
      node {
        name
        color
      }
    }
  }
}
"""


class GitHubDataFetcher:
    """Handles fetching and parsing data from the GitHub API."""

    def __init__(self, token: str):
        """Initializes the fetcher with a GitHub personal access token."""
        self.token = token

    def fetch_graphql_data(self) -> Dict[str, Any]:
        """Queries the GitHub GraphQL API to fetch user and repository stats."""
        url = "https://api.github.com/graphql"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "hhandika-stats-updater",
        }
        cursor = None
        merged_data = None

        while True:
            payload = json.dumps(
                {"query": GRAPHQL_QUERY, "variables": {"repositoriesCursor": cursor}}
            ).encode("utf-8")
            req = urllib.request.Request(
                url, data=payload, headers=headers, method="POST"
            )

            try:
                with urllib.request.urlopen(req) as res:
                    response_data = json.loads(res.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8") if e else ""
                print(
                    f"HTTP Error {e.code}: {e.reason}\nResponse: {error_body}",
                    file=sys.stderr,
                )
                raise

            if "errors" in response_data:
                print(
                    f"GraphQL Errors: {json.dumps(response_data['errors'], indent=2)}",
                    file=sys.stderr,
                )
                raise RuntimeError("GitHub API returned errors.")

            page_data = response_data["data"]
            if merged_data is None:
                merged_data = page_data
            else:
                merged_repositories = merged_data["user"]["repositories"]
                page_repositories = page_data["user"]["repositories"]
                merged_repositories["nodes"].extend(page_repositories["nodes"])
                merged_repositories["pageInfo"] = page_repositories["pageInfo"]

            page_info = page_data["user"]["repositories"]["pageInfo"]
            if not page_info["hasNextPage"]:
                return merged_data or {}
            cursor = page_info["endCursor"]

    def fetch_code_changes(
        self,
        username: str,
        repositories: List[Dict[str, Any]],
        max_attempts: int = 3,
    ) -> Dict[str, Any]:
        """Sum additions and deletions attributed to a user in public repositories."""
        totals = {"additions": 0, "deletions": 0, "commits": 0}
        repository_results = []
        failures = []

        for repository in repositories:
            name_with_owner = repository.get("nameWithOwner")
            if not name_with_owner:
                failures.append(
                    {
                        "name_with_owner": repository.get("name", "unknown"),
                        "error": "Repository owner/name is missing.",
                    }
                )
                continue

            url = f"https://api.github.com/repos/{name_with_owner}/stats/contributors"
            headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "User-Agent": "hhandika-stats-updater",
                "X-GitHub-Api-Version": "2022-11-28",
            }

            try:
                contributors = self._fetch_contributor_stats(
                    url, headers, max_attempts=max_attempts
                )
            except (
                json.JSONDecodeError,
                urllib.error.HTTPError,
                urllib.error.URLError,
                RuntimeError,
            ) as error:
                failures.append(
                    {"name_with_owner": name_with_owner, "error": str(error)[:500]}
                )
                continue

            contributor = next(
                (
                    item
                    for item in contributors
                    if (item.get("author") or {}).get("login", "").lower()
                    == username.lower()
                ),
                None,
            )
            counts = {"additions": 0, "deletions": 0, "commits": 0}
            if contributor:
                for week in contributor.get("weeks", []):
                    counts["additions"] += int(week.get("a", 0))
                    counts["deletions"] += int(week.get("d", 0))
                    counts["commits"] += int(week.get("c", 0))

            repository_results.append(
                {"name_with_owner": name_with_owner, **counts}
            )
            for key in totals:
                totals[key] += counts[key]

        return {
            "status": "partial" if failures else "complete",
            "source": "github_contributor_statistics",
            "repositories_total": len(repositories),
            "repositories_counted": len(repository_results),
            "repositories_failed": len(failures),
            "totals": totals,
            "repositories": repository_results,
            "failures": failures,
        }

    @staticmethod
    def _fetch_contributor_stats(
        url: str, headers: Dict[str, str], max_attempts: int
    ) -> List[Dict[str, Any]]:
        """Fetch contributor stats, retrying while GitHub computes a cold cache."""
        for attempt in range(max_attempts):
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request) as response:
                status = getattr(response, "status", 200)
                if status == 204:
                    return []
                if status != 202:
                    payload = json.loads(response.read().decode("utf-8"))
                    if not isinstance(payload, list):
                        raise RuntimeError("Unexpected contributor statistics response.")
                    return payload
            if attempt + 1 < max_attempts:
                time.sleep(1)
        raise RuntimeError("Contributor statistics are still being generated by GitHub.")

    def fetch_hour_counts(self, username: str) -> List[int]:
        """Counts recent push, PR, and create events per hour in ET timezone."""
        url = f"https://api.github.com/users/{username}/events?per_page=100"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "hhandika-stats-updater",
        }
        req = urllib.request.Request(url, headers=headers)
        hour_counts = [0] * 24

        try:
            with urllib.request.urlopen(req) as res:
                events = json.loads(res.read().decode("utf-8"))
        except Exception as e:
            print(
                f"Warning: Could not fetch events for peak hours calculation: {e}",
                file=sys.stderr,
            )
            return hour_counts

        for event in events:
            if event.get("type") in [
                "PushEvent",
                "PullRequestEvent",
                "CreateEvent",
            ]:
                created_at = event.get("created_at")
                if created_at:
                    match = re.search(r"T(\d{2}):", created_at)
                    if match:
                        hour = int(match.group(1))
                        # Convert UTC to Eastern Time (UTC-4)
                        et_hour = (hour - 4) % 24
                        hour_counts[et_hour] += 1
        return hour_counts

    def fetch_peak_hours(self, username: str) -> str:
        """Fetches user events and calculates peak engineering hours in ET timezone."""
        window = DataProcessor.peak_hour_window(self.fetch_hour_counts(username))
        return window[2] if window else "Afternoon (12-16)"
