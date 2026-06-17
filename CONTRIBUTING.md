# Contributing Guide: GitHub Stats Auto-Updater

This repository features an automated workflow that updates profile stats cards using Python and GitHub Actions. The stats are styled following the **Material 3 Design System** and dynamically adapt to light and dark modes natively.

---

## How It Works

1. **GitHub Actions Workflow** (`.github/workflows/update_stats.yml`):
   - Runs automatically every **Sunday at midnight**.
   - Runs on push to the `main` branch.
   - Can be triggered manually via `workflow_dispatch` in the Actions tab.
2. **Python Script** (`update_stats.py`):
   - Queries the GitHub GraphQL API for public user metrics and details for specific repositories (`nahpu/nahpu`, `hhandika/segul`, `hhandika/segui`, `hhandika/ullar`, and `mammaldiversity/mdd_app`).
   - Computes overall stars, contributions, repository counts, and aggregates language usage.
   - Generates three SVGs in the `stats/` directory:
     - `overview.svg`: Public overview stats (Stars, Contributions, CRI, etc.).
     - `languages.svg`: Top programming languages bar chart and percentage breakdown based on repository sizes.
     - `top_repos.svg`: Featured repository descriptions and their individual language composition bar charts.
   - Updates `README.md` by replacing the content between HTML placeholder comments.

---

## Statistics Descriptions

- **Total Stars**: The total number of stargazers across all of the user's public repositories.
- **Contributions**: The total number of GitHub contributions made in the last 365 days, sourced from the contribution calendar.
- **Merged PRs**: The total number of Pull Requests the user has created or contributed to.
- **Code Reviews**: The total number of Pull Request reviews submitted by the user.
- **Issues**: The total number of issues opened by the user.
- **Streak**: The longest consecutive number of days with at least one contribution in the current calendar year.
- **Peak Day**: The day of the week with the highest average number of contributions.
- **Peak Hours**: The time of day with the most commit activity, derived from analyzing commit timestamps.

---

## Local Development & Setup

### Prerequisites
- Python 3.9+
- [uv](https://github.com/astral-sh/uv) (fast Python package manager)

### Installation
Sync dependencies and set up the local virtual environment:
```bash
uv sync
```

### Running Tests
Unit tests are written with `pytest` and mock the GitHub API responses so they run instantly without hitting the network:
```bash
uv run pytest
```

### Running the Update Script Locally
To run the script locally and generate the stats:
1. Generate a [GitHub Personal Access Token (classic)](https://github.com/settings/tokens) with `read:user` and `repo` scopes.
2. Set the token in your environment and run the script:
```bash
export GITHUB_TOKEN="your_personal_access_token"
uv run python update_stats.py
```
This will fetch live public stats, regenerate the SVGs in `stats/`, and update your local `README.md`.

---

## Material 3 SVG Design Specifications

The SVGs are styled using Material 3 design tokens:
- **Rounded Corners**: A card corner radius (`rx: 12px`) is applied to matching container styles.
- **Dynamic Light/Dark Themes**: The SVGs contain built-in CSS media queries. This enables them to automatically adapt their theme colors to match the user's current GitHub interface mode:
  - **Light mode colors**: Primary (`#6750A4`), background (`#FEF7FF`), text (`#1D1B20`), outline (`#79747E`).
  - **Dark mode colors**: Primary (`#D0BCFF`), background (`#141218`), text (`#E6E1E9`), outline (`#49454F`).
- **Standard Icons**: Official GitHub Octicons are embedded directly as scalable vector paths.
- **XML Safety**: All repository descriptions and language names are XML-escaped to avoid parsing issues.
