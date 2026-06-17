import os
import tempfile

from stats.svg_generator import (
    xml_escape,
    OverviewDashboardGenerator,
    LanguagesDashboardGenerator,
    TopReposDashboardGenerator,
)
from stats.data_processor import DataProcessor
from stats.readme_updater import ReadmeUpdater


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
    )
    svg = generator.generate()

    assert "<svg" in svg
    assert "</svg>" in svg
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
    assert '<title id="titleId">Top Repositories Dashboard</title>' in svg
    assert (
        '<desc id="descId">Shows top repositories and their language composition</desc>'
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
        )

        with open(temp_path, "r", encoding="utf-8") as f:
            updated_content = f.read()

        assert "<!-- START_SECTION:github-stats -->" in updated_content
        assert "<!-- END_SECTION:github-stats -->" in updated_content
        assert 'src="assets/overview.svg"' in updated_content
        assert 'src="assets/languages.svg"' in updated_content
        assert 'src="assets/top_repos.svg"' in updated_content
        assert "*Stats reflect public repositories only" in updated_content
        assert "github-readme-stats.vercel.app" not in updated_content
    finally:
        os.remove(temp_path)
