import os
from stats.svg_generator import (
    OverviewDashboardGenerator,
    LanguagesDashboardGenerator,
    TopReposDashboardGenerator,
)

os.makedirs("assets", exist_ok=True)

mock_langs = {
    "Python": {"size": 70, "color": "#3572A5"},
    "Rust": {"size": 30, "color": "#dea584"},
}

overview_gen = OverviewDashboardGenerator(
    total_stars=123,
    total_contributions=456,
    total_repos=10,
    total_prs=10,
    total_reviews=5,
    total_issues=20,
    cri=1.5,
    streak=5,
    peak_day="Wednesday (20%)",
    peak_hours="Afternoon (12-16)",
)
with open("assets/overview.svg", "w") as f:
    f.write(overview_gen.generate())

lang_gen = LanguagesDashboardGenerator(languages=mock_langs)
with open("assets/languages.svg", "w") as f:
    f.write(lang_gen.generate())

print("Generated SVGs.")
