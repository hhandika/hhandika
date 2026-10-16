import json
import os
import tempfile
import urllib.error
import xml.etree.ElementTree as ET
from unittest.mock import patch

from datetime import datetime, timezone

from stats.svg_generator import (
    xml_escape,
    relative_age,
    ActivityDashboardGenerator,
    OverviewDashboardGenerator,
    LanguagesDashboardGenerator,
    TopReposDashboardGenerator,
)
from stats.data_processor import DataProcessor
from stats.github_fetcher import GitHubDataFetcher
from stats.readme_updater import ReadmeUpdater
from stats.summary_writer import build_summary, write_summary


def test_xml_escape():
    assert xml_escape("Hello & World") == "Hello &amp; World"
    assert xml_escape("<tag>") == "&lt;tag&gt;"
    assert xml_escape('"quotes"') == "&quot;quotes&quot;"
    assert xml_escape("'single'") == "&apos;single&apos;"
    assert xml_escape("") == ""
    assert xml_escape(None) == ""


def test_parse_languages():
    mock_repos = [
        {
            "name": "repo1",
            "languages": {
                "edges": [
                    {"size": 1000, "node": {"name": "Python", "color": "#ff0000"}},
                    {"size": 500, "node": {"name": "Rust", "color": "#00ff00"}},
                    {"size": 300, "node": {"name": "HTML", "color": "#e34c26"}},
                ]
            },
        },
        {
            "name": "repo2",
            "languages": {
                "edges": [
                    {"size": 2000, "node": {"name": "Python", "color": "#ff0000"}},
                    {"size": 1000, "node": {"name": "C++", "color": "#0000ff"}},
                ]
            },
        },
        {
            # Repo with no languages
            "name": "repo3",
            "languages": None,
        },
    ]

    processor = DataProcessor()
    langs = processor.parse_languages(mock_repos)
    assert "Python" in langs
    assert langs["Python"]["size"] == 3000
    assert langs["Python"]["color"] == "#ff0000"

    assert "Rust" in langs
    assert langs["Rust"]["size"] == 500

    assert "C++" in langs
    assert langs["C++"]["size"] == 1000

    assert "HTML" not in langs


def test_format_count():
    assert DataProcessor.format_count(999) == "999"
    assert DataProcessor.format_count(12_345) == "12.3k"
    assert DataProcessor.format_count(1_250_000) == "1.2M"


def test_code_changes_are_attributed_to_requested_user():
    repositories = [
        {"nameWithOwner": "hhandika/good"},
        {"nameWithOwner": "hhandika/broken"},
    ]

    class FakeResponse:
        status = 200

        def read(self):
            return json.dumps(
                [
                    {
                        "author": {"login": "someone-else"},
                        "weeks": [{"a": 900, "d": 800, "c": 7}],
                    },
                    {
                        "author": {"login": "HHANDIKA"},
                        "weeks": [
                            {"a": 40, "d": 12, "c": 2},
                            {"a": 5, "d": 3, "c": 1},
                        ],
                    },
                ]
            ).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    with patch(
        "urllib.request.urlopen",
        side_effect=[FakeResponse(), urllib.error.URLError("not found")],
    ):
        result = GitHubDataFetcher("token").fetch_code_changes(
            "hhandika", repositories
        )

    assert result["status"] == "partial"
    assert result["totals"] == {"additions": 45, "deletions": 15, "commits": 3}
    assert result["repositories_counted"] == 1
    assert result["repositories_failed"] == 1
    assert result["failures"][0]["name_with_owner"] == "hhandika/broken"


def test_contributor_stats_retries_accepted_response():
    class FakeResponse:
        def __init__(self, status, payload=b""):
            self.status = status
            self.payload = payload

        def read(self):
            return self.payload

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    with patch(
        "urllib.request.urlopen",
        side_effect=[FakeResponse(202), FakeResponse(200, b"[]")],
    ), patch("stats.github_fetcher.time.sleep"):
        result = GitHubDataFetcher._fetch_contributor_stats(
            "https://example.test", {}, max_attempts=2
        )

    assert result == []


def test_github_repository_pagination():
    first_page = {
        "data": {
            "user": {
                "repositories": {
                    "nodes": [{"name": "one"}],
                    "pageInfo": {"hasNextPage": True, "endCursor": "next"},
                }
            }
        }
    }
    second_page = {
        "data": {
            "user": {
                "repositories": {
                    "nodes": [{"name": "two"}],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        }
    }

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def read(self):
            return json.dumps(self.payload).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    with patch(
        "urllib.request.urlopen",
        side_effect=[FakeResponse(first_page), FakeResponse(second_page)],
    ) as urlopen:
        result = GitHubDataFetcher("token").fetch_graphql_data()

    assert [repo["name"] for repo in result["user"]["repositories"]["nodes"]] == [
        "one",
        "two",
    ]
    second_request = urlopen.call_args_list[1].args[0]
    assert json.loads(second_request.data)["variables"]["repositoriesCursor"] == "next"


def test_generate_overview_svg():
    generator = OverviewDashboardGenerator(
        total_stars=123,
        total_contributions=4567,
        total_repos=10,
        total_prs=10,
        total_reviews=5,
        total_issues=20,
        streak=5,
        code_additions=45_000,
        code_deletions=12_000,
    )
    svg = generator.generate()

    assert "<svg" in svg
    assert "</svg>" in svg
    assert 'width="400"' in svg
    ET.fromstring(svg)
    assert "Total Stars" in svg
    assert "123" in svg
    assert "Contributions" in svg
    assert "4,567" in svg
    assert "Code Changes<" in svg
    assert "+45.0k" in svg
    assert "−12.0k" in svg
    assert "var(--stats-color-additions)" in svg

    # Fixed light theme, no OS media query
    assert "#fcfcfc" in svg
    assert "@media (prefers-color-scheme: dark)" not in svg


def test_overview_dark_theme_and_partial_marker():
    generator = OverviewDashboardGenerator(
        total_stars=1,
        total_contributions=2,
        total_repos=3,
        total_prs=4,
        total_reviews=5,
        total_issues=6,
        streak=7,
        code_additions=10,
        code_deletions=0,
        code_changes_partial=True,
        theme="dark",
    )
    svg = generator.generate()

    ET.fromstring(svg)
    assert "--md-sys-color-surface: #1a1c1e;" in svg
    assert "#fcfcfc" not in svg
    assert "Code Changes*" in svg


def test_overview_highlights_streak_at_twenty_days():
    generator = OverviewDashboardGenerator(
        total_stars=123,
        total_contributions=456,
        total_repos=10,
        total_prs=10,
        total_reviews=5,
        total_issues=20,
        streak=20,
        code_additions=45_000,
        code_deletions=12_000,
    )

    svg = generator.generate()

    assert 'fill="var(--md-sys-color-tertiary)"' in svg
    assert 'class="m3-label-large m3-streak-highlight">20 Days</text>' in svg


def test_overview_does_not_highlight_streak_below_twenty_days():
    generator = OverviewDashboardGenerator(
        total_stars=123,
        total_contributions=456,
        total_repos=10,
        total_prs=10,
        total_reviews=5,
        total_issues=20,
        streak=19,
        code_additions=45_000,
        code_deletions=12_000,
    )

    svg = generator.generate()

    assert 'class="m3-label-large">19 Days</text>' in svg
    assert 'class="m3-label-large m3-streak-highlight">19 Days</text>' not in svg
    assert 'fill="var(--md-sys-color-tertiary)"' not in svg


def test_generate_languages_svg():
    mock_langs = {
        "Python": {"size": 70, "color": "#3572A5"},
        "Rust": {"size": 30, "color": "#dea584"},
    }
    generator = LanguagesDashboardGenerator(languages=mock_langs)
    svg = generator.generate()

    assert "<svg" in svg
    assert "</svg>" in svg
    assert 'width="400"' in svg
    assert 'width="352.0"' in svg
    ET.fromstring(svg)
    assert "Top Languages" in svg
    assert "Python" in svg
    assert "Rust" in svg
    assert "70.0%" in svg
    assert "30.0%" in svg


def test_generate_top_repos_svg():
    mock_repos_data = [
        {
            "name": "segul",
            "owner": {"login": "hhandika"},
            "description": "Genomic CLI tool",
            "stargazerCount": 1234,
            "pushedAt": "2026-10-12T08:00:00Z",
            "languages": {
                "edges": [
                    {"size": 1000, "node": {"name": "Rust", "color": "#dea584"}},
                    {"size": 1, "node": {"name": "Python", "color": "#3572A5"}},
                ]
            },
        },
        None,  # simulate one missing repo
        {
            "name": "nahpu",
            "owner": {"login": "nahpu"},
            "description": "Biodiversity field data management app",
            "languages": {
                "edges": [{"size": 2000, "node": {"name": "Dart", "color": "#00B4AB"}}]
            },
        },
    ]

    top_repos_config = [
        ("hhandika", "segul"),
        ("hhandika", "ullar"),
        ("nahpu", "nahpu"),
    ]

    generator = TopReposDashboardGenerator(
        top_repos=top_repos_config,
        repos_data=mock_repos_data,
        now=datetime(2026, 10, 15, 12, tzinfo=timezone.utc),
    )
    svg = generator.generate()

    assert "<svg" in svg
    assert 'width="816"' in svg
    assert 'width="376"' in svg
    ET.fromstring(svg)
    assert "hhandika/segul" in svg
    assert "Genomic CLI tool" in svg
    assert "#dea584" in svg  # Rust color in bar chart
    assert "★ 1,234 · updated 3d ago" in svg
    # Languages under 1% stay in the bar but are left out of the legend
    assert "Python 0.1%" not in svg
    # Light swatches get an outline in the light theme
    assert 'fill="#dea584" stroke="var(--md-sys-color-outline)"' in svg

    assert "nahpu/nahpu" in svg
    assert "Biodiversity field data" in svg
    assert "#00B4AB" in svg  # Dart color in bar chart

    # Missing repo message should be handled without crashing
    assert "Repository not found or private." in svg

    # Test accessibility tags
    assert 'role="img"' in svg
    assert '<title id="titleId">Selected Repositories Dashboard</title>' in svg
    assert (
        '<desc id="descId">Shows selected repositories and their language composition</desc>'
        in svg
    )


def test_update_readme():
    initial_content = """# My Profile
Hello there!

[![Handika's GitHub stats](https://github-readme-stats.vercel.app/api?username=hhandika&theme=vue-dark&card_width=420)](https://github.com/anuraghazra/github-readme-stats)

![Top Langs](https://github-readme-stats.vercel.app/api/top-langs/?username=hhandika&hide_progress=false&langs_count=10&layout=compact&hide=html,ruby,cmake,css,mdx&theme=vue-dark&card_width=420)

Some footer.
"""

    # Create temp file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, encoding="utf-8") as temp:
        temp.write(initial_content)
        temp_path = temp.name

    try:
        updater = ReadmeUpdater()
        updater.update(
            [
                [
                    ("assets/overview", "GitHub Stats", "49%"),
                    ("assets/languages", "Top Languages", "49%"),
                ],
                [("assets/top_repos", "Selected Repositories", "98%")],
            ],
            readme_path=temp_path,
            code_changes_partial=True,
            total_repos=42,
            counted_repos=40,
        )

        with open(temp_path, "r", encoding="utf-8") as f:
            updated_content = f.read()

        assert "<!-- START_SECTION:github-stats -->" in updated_content
        assert "<!-- END_SECTION:github-stats -->" in updated_content
        assert 'src="assets/overview-light.svg"' in updated_content
        assert 'srcset="assets/overview-dark.svg"' in updated_content
        assert 'src="assets/languages-light.svg"' in updated_content
        assert 'src="assets/top_repos-light.svg"' in updated_content
        assert '<source media="(prefers-color-scheme: dark)"' in updated_content
        assert 'width="49%"' in updated_content
        assert updated_content.count('<p align="left">\n  <picture>') == 2
        assert "*Code changes are partial" in updated_content
        assert "data/stats.json" in updated_content
        assert "Stats reflect public repositories only (40 of 42 repositories counted)." in updated_content
        assert "github-readme-stats.vercel.app" not in updated_content
    finally:
        os.remove(temp_path)


def test_write_complete_stats_summary():
    code_changes = {
        "status": "complete",
        "source": "github_contributor_statistics",
        "repositories_total": 1,
        "repositories_counted": 1,
        "repositories_failed": 0,
        "totals": {"additions": 40, "deletions": 12, "commits": 3},
        "repositories": [],
        "failures": [],
    }
    repository = {
        "description": "Example",
        "languages": {
            "edges": [
                {"size": 75, "node": {"name": "Python", "color": "#3572A5"}}
            ]
        },
    }
    summary = build_summary(
        username="hhandika",
        overview={"total_stars": 3, "code_additions": 40, "code_deletions": 12},
        languages={"Python": {"size": 75, "color": "#3572A5"}},
        top_repos=[("hhandika", "example")],
        repos_data=[repository],
        code_changes=code_changes,
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "data", "stats.json")
        write_summary(summary, output_path)
        with open(output_path, encoding="utf-8") as summary_file:
            written = json.load(summary_file)

    assert written["schema_version"] == 2
    assert written["overview"]["code_additions"] == 40
    assert written["overview"]["code_deletions"] == 12
    assert written["code_changes"]["totals"]["additions"] == 40
    assert written["language_statistics"]["languages"]["Python"]["percentage"] == 100.0
    assert written["featured_repositories"][0]["name_with_owner"] == "hhandika/example"


def test_weekday_totals_and_peak_hour_window():
    calendar = {
        "weeks": [
            {
                "contributionDays": [
                    {"contributionCount": 2, "date": "2026-01-04", "weekday": 0},
                    {"contributionCount": 5, "date": "2026-01-10", "weekday": 6},
                ]
            },
            {
                "contributionDays": [
                    {"contributionCount": 1, "date": "2026-01-17", "weekday": 6},
                ]
            },
        ]
    }
    assert DataProcessor.weekday_totals(calendar) == [2, 0, 0, 0, 0, 0, 6]
    assert DataProcessor.calendar_days(calendar) == [
        {"date": "2026-01-04", "count": 2},
        {"date": "2026-01-10", "count": 5},
        {"date": "2026-01-17", "count": 1},
    ]

    hours = [0] * 24
    hours[13] = 4
    hours[21] = 2
    assert DataProcessor.peak_hour_window(hours) == (12, 16, "Afternoon")
    assert DataProcessor.peak_hour_window([0] * 24) is None


def test_generate_activity_svg():
    hours = [0] * 24
    hours[14] = 3
    hours[9] = 1
    generator = ActivityDashboardGenerator(
        weekday_counts=[10, 20, 20, 20, 20, 20, 40], hour_counts=hours
    )
    svg = generator.generate()

    ET.fromstring(svg)
    assert 'width="816"' in svg
    assert "Peak: Saturday (27%)" in svg
    assert "Peak: Afternoon" in svg
    assert svg.index(">Mon<") < svg.index(">Sun<")
    assert "var(--md-sys-color-tertiary)" in svg


def test_generate_activity_svg_without_data():
    svg = ActivityDashboardGenerator(
        weekday_counts=[0] * 7, hour_counts=[0] * 24, theme="dark"
    ).generate()

    ET.fromstring(svg)
    assert "No contributions yet" in svg
    assert "No recent event data" in svg


def test_relative_age():
    now = datetime(2026, 10, 15, 12, tzinfo=timezone.utc)
    assert relative_age("2026-10-15T08:00:00Z", now) == "today"
    assert relative_age("2026-10-05T12:00:00Z", now) == "10d ago"
    assert relative_age("2026-06-15T12:00:00Z", now) == "4mo ago"
    assert relative_age("2024-10-01T12:00:00Z", now) == "2y ago"
    assert relative_age(None, now) == ""
