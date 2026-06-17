"""Handles fetching and parsing data from the GitHub API."""

import json
import re
import sys
import urllib.request
from typing import Dict, Any

GRAPHQL_QUERY = """
query {
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
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, orderBy: {field: STARGAZERS, direction: DESC}) {
      nodes {
        name
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
}

fragment RepoFields on Repository {
  name
  owner {
    login
  }
  description
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
        payload = json.dumps({"query": GRAPHQL_QUERY}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req) as res:
                response_data = json.loads(res.read().decode("utf-8"))
                if "errors" in response_data:
                    print(
                        f"GraphQL Errors: {json.dumps(response_data['errors'], indent=2)}",
                        file=sys.stderr,
                    )
                    raise RuntimeError("GitHub API returned errors.")
                return response_data["data"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e else ""
            print(
                f"HTTP Error {e.code}: {e.reason}\nResponse: {error_body}",
                file=sys.stderr,
            )
            raise

    def fetch_peak_hours(self, username: str) -> str:
        """Fetches user events and calculates peak engineering hours in ET timezone."""
        url = f"https://api.github.com/users/{username}/events?per_page=100"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "hhandika-stats-updater",
        }
        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req) as res:
                events = json.loads(res.read().decode("utf-8"))

            hour_counts = {h: 0 for h in range(24)}
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

            total_events = sum(hour_counts.values())
            if total_events == 0:
                return "Afternoon (12-16)"

            windows = [
                (0, 4, "Late Night"),
                (4, 8, "Early Morning"),
                (8, 12, "Morning"),
                (12, 16, "Afternoon"),
                (16, 20, "Late Afternoon"),
                (20, 24, "Evening"),
            ]

            window_scores = []
            for start, end, label in windows:
                score = sum(hour_counts[h] for h in range(start, end))
                window_scores.append((score, label))

            return max(window_scores, key=lambda x: x[0])[1]
        except Exception as e:
            print(
                f"Warning: Could not fetch events for peak hours calculation: {e}",
                file=sys.stderr,
            )
            return "Afternoon (12-16)"
