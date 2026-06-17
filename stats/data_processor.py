"""Processes raw GitHub API data into statistical metrics."""

from typing import Dict, Any, List, Tuple

EXCLUDED_LANGUAGES = {
    "html",
    "css",
    "cmake",
    "markdown",
    "dockerfile",
    "makefile",
    "tex",
    "scss",
    "sass",
    "yaml",
    "yml",
    "json",
    "toml",
    "ini",
    "csv",
    "xml",
    "plaintext",
    "text",
    "gitattributes",
    "gitignore",
}


class DataProcessor:
    """Processes raw GitHub API data into statistical metrics."""

    @staticmethod
    def parse_languages(repos: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Aggregates languages and sizes in bytes, filtering out markup/configs."""
        languages: Dict[str, Dict[str, Any]] = {}
        for repo in repos:
            if not repo or "languages" not in repo or not repo["languages"]:
                continue
            for edge in repo["languages"]["edges"]:
                lang_node = edge["node"]
                lang_name = lang_node["name"]
                lang_color = lang_node["color"]
                size = edge["size"]

                if lang_name.lower() in EXCLUDED_LANGUAGES:
                    continue

                if lang_name not in languages:
                    languages[lang_name] = {"size": 0, "color": lang_color}
                languages[lang_name]["size"] += size
        return languages

    @staticmethod
    def calculate_calendar_metrics(calendar_data: Dict[str, Any]) -> Tuple[int, str]:
        """Calculates active streak and peak contribution day from calendar data."""
        weeks = calendar_data.get("weeks", [])
        all_days = []

        weekday_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        weekday_names = {
            0: "Sunday",
            1: "Monday",
            2: "Tuesday",
            3: "Wednesday",
            4: "Thursday",
            5: "Friday",
            6: "Saturday",
        }

        for week in weeks:
            for day in week.get("contributionDays", []):
                count = day.get("contributionCount", 0)
                date_str = day.get("date")
                weekday = day.get("weekday")
                all_days.append((date_str, count))
                weekday_counts[weekday] += count

        all_days.sort(key=lambda x: x[0])

        # Calculate streak (consecutive active days walking backward)
        current_streak = 0
        for _, count in reversed(all_days):
            if count > 0:
                current_streak += 1
            else:
                if current_streak > 0:
                    break

        peak_weekday_idx = max(weekday_counts, key=weekday_counts.get)
        peak_weekday = weekday_names[peak_weekday_idx]

        total_contribs = sum(weekday_counts.values())
        if total_contribs > 0:
            peak_pct = (weekday_counts[peak_weekday_idx] / total_contribs) * 100
            peak_day_str = f"{peak_weekday} ({peak_pct:.0f}%)"
        else:
            peak_day_str = "None"

        return current_streak, peak_day_str
