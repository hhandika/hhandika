import json
import os
import tempfile
import xml.etree.ElementTree as ET
from subprocess import CalledProcessError, CompletedProcess
from unittest.mock import patch

from stats.svg_generator import (
    xml_escape,
    OverviewDashboardGenerator,
    LanguagesDashboardGenerator,
    TopReposDashboardGenerator,
)
from stats.data_processor import DataProcessor
from stats.github_fetcher import GitHubDataFetcher
from stats.readme_updater import ReadmeUpdater
from stats.source_line_counter import SourceLineCounter
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


def test_format_lines_of_code():
    assert DataProcessor.format_lines_of_code(999) == "999"
    assert DataProcessor.format_lines_of_code(12_345) == "12.3k"
    assert DataProcessor.format_lines_of_code(1_250_000) == "1.2M"


def test_parse_cloc_output_uses_code_lines_and_excludes_markup():
    result = SourceLineCounter._parse_cloc_output(
        json.dumps(
            {
                "header": {"cloc_url": "example"},
                "Python": {"nFiles": 2, "blank": 5, "comment": 7, "code": 41},
                "Rust": {"nFiles": 1, "blank": 2, "comment": 3, "code": 29},
                "Markdown": {"nFiles": 3, "blank": 1, "comment": 0, "code": 100},
                "SUM": {"nFiles": 6, "blank": 8, "comment": 10, "code": 170},
            }
        )
    )

    assert result["totals"] == {
        "files": 3,
        "blank": 7,
        "comment": 10,
        "code": 70,
    }
    assert set(result["languages"]) == {"Python", "Rust"}


def test_source_line_counter_publishes_partial_results():
    repositories = [
        {"nameWithOwner": "hhandika/good", "url": "https://github.com/hhandika/good"},
        {"nameWithOwner": "hhandika/broken", "url": "https://github.com/hhandika/broken"},
    ]
    cloc_output = json.dumps(
        {
            "Python": {"nFiles": 2, "blank": 5, "comment": 3, "code": 40},
            "SUM": {"nFiles": 2, "blank": 5, "comment": 3, "code": 40},
        }
    )
    process_results = [
        CompletedProcess(["cloc", "--version"], 0, "2.02", ""),
        CompletedProcess(["git", "clone"], 0, "", ""),
        CompletedProcess(["cloc"], 0, cloc_output, ""),
        CalledProcessError(128, ["git", "clone"], stderr="not found"),
    ]

    with patch("stats.source_line_counter.shutil.which", return_value="/usr/bin/cloc"):
        with patch(
            "stats.source_line_counter.subprocess.run", side_effect=process_results
        ):
            result = SourceLineCounter().count_repositories(repositories)

    assert result["status"] == "partial"
    assert result["totals"]["code"] == 40
    assert result["repositories_counted"] == 1
    assert result["repositories_failed"] == 1
    assert result["failures"][0]["name_with_owner"] == "hhandika/broken"


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
        total_contributions=456,
        total_repos=10,
        total_prs=10,
        total_reviews=5,
        total_issues=20,
        streak=5,
        peak_day="Wednesday (20%)",
        peak_hours="Afternoon (12-16)",
        total_loc="45k",
    )
    svg = generator.generate()

    assert "<svg" in svg
    assert "</svg>" in svg
    assert 'width="480"' in svg
    ET.fromstring(svg)
    assert "Total Stars" in svg
    assert "123" in svg
    assert "Contributions" in svg
    assert "456" in svg

    # Test media query stylesheet exists
    assert "@media (prefers-color-scheme: dark)" in svg


def test_generate_languages_svg():
    mock_langs = {
        "Python": {"size": 70, "color": "#3572A5"},
        "Rust": {"size": 30, "color": "#dea584"},
    }
    generator = LanguagesDashboardGenerator(languages=mock_langs)
    svg = generator.generate()

    assert "<svg" in svg
    assert "</svg>" in svg
    assert 'width="480"' in svg
    assert 'width="432.0"' in svg
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
            "languages": {
                "edges": [{"size": 1000, "node": {"name": "Rust", "color": "#dea584"}}]
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
        top_repos=top_repos_config, repos_data=mock_repos_data
    )
    svg = generator.generate()

    assert "<svg" in svg
    assert 'width="480"' in svg
    assert 'width="432"' in svg
    ET.fromstring(svg)
    assert "hhandika/segul" in svg
    assert "Genomic CLI tool" in svg
    assert "#dea584" in svg  # Rust color in bar chart

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
            overview_svg_path="assets/overview.svg",
            languages_svg_path="assets/languages.svg",
            top_repos_svg_path="assets/top_repos.svg",
            readme_path=temp_path,
            line_count_partial=True,
        )

        with open(temp_path, "r", encoding="utf-8") as f:
            updated_content = f.read()

        assert "<!-- START_SECTION:github-stats -->" in updated_content
        assert "<!-- END_SECTION:github-stats -->" in updated_content
        assert 'src="assets/overview.svg"' in updated_content
        assert 'src="assets/languages.svg"' in updated_content
        assert 'src="assets/top_repos.svg"' in updated_content
        assert 'width="480"' in updated_content
        assert "*Line count is partial" in updated_content
        assert "data/stats.json" in updated_content
        assert "Stats reflect public repositories only" in updated_content
        assert "github-readme-stats.vercel.app" not in updated_content
    finally:
        os.remove(temp_path)


def test_write_complete_stats_summary():
    line_count = {
        "status": "complete",
        "counter": {"name": "cloc", "version": "2.02"},
        "repositories_total": 1,
        "repositories_counted": 1,
        "repositories_failed": 0,
        "totals": {"files": 2, "blank": 5, "comment": 3, "code": 40},
        "languages": {
            "Python": {"files": 2, "blank": 5, "comment": 3, "code": 40}
        },
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
        overview={"total_stars": 3, "total_lines_of_code": 40},
        languages={"Python": {"size": 75, "color": "#3572A5"}},
        top_repos=[("hhandika", "example")],
        repos_data=[repository],
        line_count=line_count,
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "data", "stats.json")
        write_summary(summary, output_path)
        with open(output_path, encoding="utf-8") as summary_file:
            written = json.load(summary_file)

    assert written["schema_version"] == 1
    assert written["overview"]["total_lines_of_code"] == 40
    assert written["source_line_count"]["totals"]["code"] == 40
    assert written["language_statistics"]["languages"]["Python"]["percentage"] == 100.0
    assert written["featured_repositories"][0]["name_with_owner"] == "hhandika/example"
