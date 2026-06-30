"""Handles updating the README.md file with generated SVGs."""

import os
import re
from datetime import datetime


class ReadmeUpdater:
    """Handles updating the README.md file with the newly generated SVGs."""

    @staticmethod
    def update(
        overview_svg_path: str,
        languages_svg_path: str,
        top_repos_svg_path: str,
        readme_path: str = "README.md",
    ) -> None:
        """Replaces content between placeholders in README.md with generated SVG images."""
        if not os.path.exists(readme_path):
            print(f"Warning: {readme_path} not found. Skipping README update.")
            return

        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        today_str = datetime.now().strftime("%B %d, %Y")

        new_stats_content = (
            "<!-- START_SECTION:github-stats -->\n"
            '<p align="left">\n'
            f'  <img src="{overview_svg_path}" alt="GitHub Stats" width="600" />\n'
            f'  <img src="{languages_svg_path}" alt="Top Languages" width="600" />\n'
            f'  <img src="{top_repos_svg_path}" alt="Selected Repositories" width="600" />\n'
            "</p>\n"
            f'<p align="left"><sub>*Stats reflect public repositories only. Updates daily • Latest update: {today_str}</sub></p>\n'
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
