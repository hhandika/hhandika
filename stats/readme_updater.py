"""Handles updating the README.md file with generated SVGs."""

import os
import re
from datetime import datetime
from typing import List, Optional, Tuple

# (path without "-light.svg"/"-dark.svg" suffix, alt text, width attribute)
Card = Tuple[str, str, str]


class ReadmeUpdater:
    """Handles updating the README.md file with the newly generated SVGs."""

    @staticmethod
    def picture(card: Card) -> str:
        """Returns a <picture> that follows the viewer's GitHub color theme."""
        base_path, alt, width = card
        return (
            "  <picture>\n"
            f'    <source media="(prefers-color-scheme: dark)" srcset="{base_path}-dark.svg" />\n'
            f'    <img src="{base_path}-light.svg" alt="{alt}" width="{width}" />\n'
            "  </picture>\n"
        )

    @staticmethod
    def update(
        card_rows: List[List[Card]],
        readme_path: str = "README.md",
        code_changes_partial: bool = False,
        summary_path: str = "data/stats.json",
        total_repos: Optional[int] = None,
        counted_repos: Optional[int] = None,
    ) -> None:
        """Replaces content between placeholders in README.md with generated SVG images."""
        if not os.path.exists(readme_path):
            print(f"Warning: {readme_path} not found. Skipping README update.")
            return

        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        today_str = datetime.now().strftime("%B %d, %Y")

        partial_footnote = ""
        if code_changes_partial:
            partial_footnote = (
                '<p align="left"><sub>*Code changes are partial; omitted repositories '
                f'are listed in <a href="{summary_path}">{summary_path}</a>.</sub></p>\n'
            )

        repos_note = ""
        if total_repos is not None:
            label = "repository" if total_repos == 1 else "repositories"
            if counted_repos is None:
                repos_note = f" ({total_repos} {label} counted)"
            else:
                repos_note = f" ({counted_repos} of {total_repos} {label} counted)"

        rows_html = "".join(
            '<p align="left">\n'
            + "".join(ReadmeUpdater.picture(card) for card in row)
            + "</p>\n"
            for row in card_rows
        )

        new_stats_content = (
            "<!-- START_SECTION:github-stats -->\n"
            f"{rows_html}"
            f"{partial_footnote}"
            f'<p align="left"><sub>Stats reflect public repositories only{repos_note}. Updates daily • Latest update: {today_str}</sub></p>\n'
            "<!-- END_SECTION:github-stats -->"
        )

        pattern = r"<!--\s*START_SECTION:github-stats\s*-->.*?<!--\s*END_SECTION:github-stats\s*-->"
        updated_content, count = re.subn(
            pattern, new_stats_content, content, flags=re.DOTALL
        )

        if count == 0:
            vercel_pattern = r"\[\!\[Handika's GitHub stats\].*?theme=vue-dark.*\n.*\n\!\[Top Langs\].*?theme=vue-dark.*"
            updated_content, vercel_count = re.subn(
                vercel_pattern, new_stats_content, content
            )

            if vercel_count == 0:
                print(
                    "Warning: Placeholders not found in README.md. Appending stats to the end."
                )
                updated_content = content.rstrip() + "\n\n" + new_stats_content + "\n"

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print("README.md successfully updated!")
