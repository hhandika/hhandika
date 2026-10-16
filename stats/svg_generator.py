"""Base class and concrete implementations for SVG generators."""

from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
from stats.data_processor import DataProcessor
from stats.m3_design_system import M3Tokens

FALLBACK_COLOR = "#8e918f"

# Approximate advance of one m3-label-medium character (12px, 0.5px tracking)
LABEL_CHAR_WIDTH = 7.2

# Shorter legend names for languages whose full name crowds the repo cards
LANGUAGE_ALIASES = {"Jupyter Notebook": "Jupyter"}


def xml_escape(text: str) -> str:
    """Escapes special XML characters in string to prevent breaking SVG structure."""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def relative_luminance(color: str) -> float:
    """Returns the WCAG relative luminance of a #rrggbb color."""
    hex_color = color.lstrip("#")
    if len(hex_color) != 6:
        return 0.5
    channels = []
    for i in (0, 2, 4):
        c = int(hex_color[i : i + 2], 16) / 255
        channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def relative_age(timestamp: Optional[str], now: datetime) -> str:
    """Formats an ISO 8601 timestamp as a short age such as "3d ago"."""
    if not timestamp:
        return ""
    then = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    days = (now - then).days
    if days < 1:
        return "today"
    if days < 30:
        return f"{days}d ago"
    if days < 365:
        return f"{days // 30}mo ago"
    return f"{days // 365}y ago"


class M3SVGGenerator:
    """Base class for Material 3 SVG generation."""

    def __init__(
        self,
        width: int,
        height: int,
        title: str = "GitHub Stats",
        desc: str = "GitHub statistics dashboard",
        theme: str = "light",
    ):
        """Initializes the generator with SVG dimensions and color theme."""
        self.width = width
        self.height = height
        self.title = title
        self.desc = desc
        self.theme = theme

    def generate(self) -> str:
        """Generates the final SVG string. Must be implemented by subclasses."""
        raise NotImplementedError

    def _get_svg_header(self) -> str:
        """Returns the SVG root element and styles."""
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}" fill="none" role="img" aria-labelledby="titleId descId">\n'
            f'  <title id="titleId">{xml_escape(self.title)}</title>\n'
            f'  <desc id="descId">{xml_escape(self.desc)}</desc>\n'
            f"{M3Tokens.get_style_block(self.theme)}\n"
        )

    def _get_svg_footer(self) -> str:
        """Returns the closing SVG tag."""
        return "</svg>\n"

    def _get_background_card(self) -> str:
        """Returns the main large container card."""
        return f'<rect class="m3-container-large" x="0.5" y="0.5" width="{self.width - 1}" height="{self.height - 1}" />\n'

    def _get_title(self, title: str, subtitle: str) -> str:
        """Returns the card headline and supporting text."""
        return (
            f'  <text x="24" y="36" class="m3-headline-small">{xml_escape(title)}</text>\n'
            f'  <text x="24" y="56" class="m3-body-small">{xml_escape(subtitle)}</text>\n'
        )

    def _swatch_stroke(self, color: str) -> str:
        """Outlines swatches that would fade into the card surface."""
        luminance = relative_luminance(color)
        if (self.theme == "light" and luminance > 0.4) or (
            self.theme == "dark" and luminance < 0.03
        ):
            return ' stroke="var(--md-sys-color-outline)" stroke-width="1"'
        return ""

    def _get_segmented_bar(
        self,
        clip_id: str,
        x: float,
        y: float,
        width: float,
        height: float,
        segments: List[Tuple[float, str]],
    ) -> str:
        """Returns a rounded stacked bar with a 2px gap between segments."""
        total = sum(value for value, _ in segments)
        rects = []
        if total > 0:
            visible = [(v, c) for v, c in segments if v / total * width >= 0.5]
            current_x = x
            for idx, (value, color) in enumerate(visible):
                w = value / total * width
                is_last = idx == len(visible) - 1
                drawn = w if is_last else max(w - 2, 0.5)
                rects.append(
                    f'<rect x="{current_x:.2f}" y="{y}" width="{drawn:.2f}" height="{height}" fill="{color}" />'
                )
                current_x += w
        content = "\n      ".join(rects)
        return (
            f'  <clipPath id="{clip_id}">\n'
            f'    <rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{height / 4:g}" />\n'
            "  </clipPath>\n"
            f'  <g clip-path="url(#{clip_id})">\n'
            f'    <rect x="{x}" y="{y}" width="{width}" height="{height}" fill="var(--md-sys-color-surface-variant)" />\n'
            f"      {content}\n"
            "  </g>\n"
        )


class OverviewDashboardGenerator(M3SVGGenerator):
    """Generates the Overview SVG dashboard."""

    def __init__(
        self,
        total_stars: int,
        total_contributions: int,
        total_repos: int,
        total_prs: int,
        total_reviews: int,
        total_issues: int,
        streak: int,
        code_additions: int,
        code_deletions: int,
        code_changes_partial: bool = False,
        theme: str = "light",
    ):
        """Initializes with all overview metrics."""
        super().__init__(
            width=400,
            height=240,
            desc="GitHub statistics dashboard. Updates daily.",
            theme=theme,
        )
        self.total_stars = total_stars
        self.total_contributions = total_contributions
        self.total_repos = total_repos
        self.total_prs = total_prs
        self.total_reviews = total_reviews
        self.total_issues = total_issues
        self.streak = streak
        self.code_additions = code_additions
        self.code_deletions = code_deletions
        self.code_changes_partial = code_changes_partial

    def generate(self) -> str:
        """Generates the Overview SVG."""
        content = [
            self._get_svg_header(),
            self._get_background_card(),
            self._get_title("GitHub Profile Overview", "Public data only • Updates daily"),
            self._get_grid(),
            self._get_code_changes(),
            self._get_svg_footer(),
        ]
        return "".join(content)

    def _get_grid(self) -> str:
        """Returns the 3x2 grid with stats."""
        grid_html = ""

        # Row 1
        grid_html += self._get_stat_item(
            24, 84, "stars", "Total Stars", f"{self.total_stars:,}"
        )
        grid_html += self._get_stat_item(
            148, 84, "contributions", "Contributions", f"{self.total_contributions:,}"
        )
        grid_html += self._get_stat_item(
            272,
            84,
            "streak",
            "Streak",
            f"{self.streak:,} Days",
            highlight=self.streak >= 20,
        )

        # Row 2
        grid_html += self._get_stat_item(
            24, 134, "prs", "Merged PRs", f"{self.total_prs:,}"
        )
        grid_html += self._get_stat_item(
            148, 134, "reviews", "Code Reviews", f"{self.total_reviews:,}"
        )
        grid_html += self._get_stat_item(
            272, 134, "issues", "Issues", f"{self.total_issues:,}"
        )

        return grid_html

    def _get_code_changes(self) -> str:
        """Returns code changes as an additions/deletions bar with labels."""
        label = "Code Changes*" if self.code_changes_partial else "Code Changes"
        additions = DataProcessor.format_count(self.code_additions)
        deletions = DataProcessor.format_count(self.code_deletions)
        icon_path = M3Tokens.ICONS["code"]
        return (
            '  <g transform="translate(24, 184)">\n'
            '    <svg x="0" y="-3" width="18" height="18" viewBox="0 0 24 24" fill="var(--md-sys-color-primary)">\n'
            f'      <path d="{icon_path}"/>\n'
            "    </svg>\n"
            f'    <text x="24" y="11" class="m3-body-small">{label}</text>\n'
            '    <text x="352" y="12" text-anchor="end" class="m3-label-large">'
            f'<tspan style="fill: var(--stats-color-additions);">+{additions}</tspan>'
            f'<tspan dx="8" style="fill: var(--stats-color-deletions);">−{deletions}</tspan></text>\n'
            "  </g>\n"
            + self._get_segmented_bar(
                "code-changes-clip",
                24,
                208,
                352,
                6,
                [
                    (self.code_additions, "var(--stats-color-additions)"),
                    (self.code_deletions, "var(--stats-color-deletions)"),
                ],
            )
        )

    def _get_stat_item(
        self,
        x: int,
        y: int,
        icon_name: str,
        label: str,
        value: str,
        highlight: bool = False,
    ) -> str:
        """Returns a single stat item with an icon."""
        icon_path = M3Tokens.ICONS.get(icon_name, "")
        icon_fill = (
            "var(--md-sys-color-tertiary)"
            if highlight
            else "var(--md-sys-color-primary)"
        )
        value_class = (
            "m3-label-large m3-streak-highlight"
            if highlight
            else "m3-label-large"
        )
        return (
            f'  <g transform="translate({x}, {y})">\n'
            f'    <svg x="0" y="-3" width="18" height="18" viewBox="0 0 24 24" fill="{icon_fill}">\n'
            f'      <path d="{icon_path}"/>\n'
            f"    </svg>\n"
            f'    <text x="24" y="11" class="m3-body-small">{label}</text>\n'
            f'    <text x="24" y="31" class="{value_class}">{value}</text>\n'
            f"  </g>\n"
        )


class LanguagesDashboardGenerator(M3SVGGenerator):
    """Generates the Languages SVG dashboard."""

    def __init__(
        self,
        languages: Dict[str, Dict[str, Any]],
        theme: str = "light",
    ):
        """Initializes with languages data."""
        super().__init__(
            width=400,
            height=240,
            title="Top Languages Dashboard",
            desc="Shows a bar chart of top programming languages used",
            theme=theme,
        )
        self.languages = languages

    def generate(self) -> str:
        """Generates the Languages SVG."""
        content = [
            self._get_svg_header(),
            self._get_background_card(),
            self._get_title("Top Languages", "Based on repository size"),
            self._get_language_breakdown(),
            self._get_svg_footer(),
        ]
        return "".join(content)

    def _get_language_breakdown(self) -> str:
        """Returns the language bar and legend in two columns."""
        total_size = sum(lang["size"] for lang in self.languages.values())
        total_bar_width = 352.0

        if total_size == 0:
            return (
                self._get_segmented_bar("lang-bar-clip", 24, 84, total_bar_width, 12, [])
                + '  <g transform="translate(24, 116)">\n'
                '    <circle cx="6" cy="6" r="6" fill="var(--md-sys-color-outline-variant)" />\n'
                '    <text x="24" y="11" class="m3-body-large">No data</text>\n'
                "  </g>\n"
            )

        sorted_langs = sorted(
            self.languages.items(), key=lambda x: x[1]["size"], reverse=True
        )
        top_6 = sorted_langs[:6]
        other_size = sum(lang[1]["size"] for lang in sorted_langs[6:])

        legend_data = []
        for name, data in top_6:
            pct = (data["size"] / total_size) * 100
            legend_data.append(
                {"name": name, "pct": pct, "color": data["color"] or FALLBACK_COLOR}
            )

        if other_size > 0:
            pct_other = (other_size / total_size) * 100
            legend_data.append(
                {"name": "Other", "pct": pct_other, "color": FALLBACK_COLOR}
            )

        legend_items = []
        for idx, item in enumerate(legend_data):
            col = idx % 2
            row = idx // 2
            item_x = 24 + (col * 188)
            item_y = 116 + (row * 28)

            lang_name = item["name"]
            if len(lang_name) > 15:
                display_name = lang_name[:12] + "..."
            else:
                display_name = lang_name

            escaped_name = xml_escape(display_name)
            pct_text = f"{item['pct']:.1f}%"

            legend_items.append(
                f'  <g transform="translate({item_x}, {item_y})">\n'
                f'    <circle cx="6" cy="6" r="5.5" fill="{item["color"]}"{self._swatch_stroke(item["color"])} />\n'
                f'    <text x="20" y="11" class="m3-body-medium">{escaped_name}</text>\n'
                f'    <text x="164" y="11" text-anchor="end" class="m3-label-medium">{pct_text}</text>\n'
                f"  </g>\n"
            )

        return self._get_segmented_bar(
            "lang-bar-clip",
            24,
            84,
            total_bar_width,
            12,
            [(item["pct"], item["color"]) for item in legend_data],
        ) + "".join(legend_items)


class ActivityDashboardGenerator(M3SVGGenerator):
    """Generates the Activity Rhythm SVG dashboard (weekday and hour charts)."""

    WEEKDAY_ORDER = [1, 2, 3, 4, 5, 6, 0]  # Monday first; data is Sunday-indexed
    WEEKDAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    WEEKDAY_FULL_NAMES = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]
    PANEL_WIDTH = 352
    BASELINE = 166
    MAX_BAR_HEIGHT = 52

    def __init__(
        self,
        weekday_counts: List[int],
        hour_counts: List[int],
        theme: str = "light",
    ):
        """Initializes with Sunday-indexed weekday totals and 24 hourly counts (ET)."""
        super().__init__(
            width=816,
            height=196,
            title="Activity Rhythm Dashboard",
            desc="Shows contributions by weekday and recent activity by hour of day",
            theme=theme,
        )
        self.weekday_counts = weekday_counts
        self.hour_counts = hour_counts

    def generate(self) -> str:
        """Generates the Activity Rhythm SVG."""
        content = [
            self._get_svg_header(),
            self._get_background_card(),
            self._get_title(
                "Activity Rhythm",
                "Contributions by weekday (past year) • Recent events by hour (ET)",
            ),
            self._get_weekday_chart(24),
            self._get_hour_chart(self.width - 24 - self.PANEL_WIDTH),
            self._get_svg_footer(),
        ]
        return "".join(content)

    def _panel_header(self, x: int, title: str, peak: str) -> str:
        """Returns a panel title with its peak summary right-aligned."""
        return (
            f'  <text x="{x}" y="88" class="m3-title-small">{title}</text>\n'
            f'  <text x="{x + self.PANEL_WIDTH}" y="88" text-anchor="end" class="m3-label-medium">{xml_escape(peak)}</text>\n'
        )

    def _bar(self, x: float, width: float, value: int, max_value: int, peak: bool) -> str:
        """Returns one column bar on the shared baseline, with a stub for zero."""
        if value <= 0 or max_value <= 0:
            return (
                f'  <rect x="{x:.2f}" y="{self.BASELINE - 2}" width="{width:.2f}" height="2" '
                'fill="var(--md-sys-color-surface-variant)" />\n'
            )
        h = max(value / max_value * self.MAX_BAR_HEIGHT, 3)
        fill = "var(--md-sys-color-tertiary)" if peak else "var(--md-sys-color-primary)"
        return (
            f'  <rect x="{x:.2f}" y="{self.BASELINE - h:.2f}" width="{width:.2f}" height="{h:.2f}" '
            f'rx="2" fill="{fill}" />\n'
        )

    def _get_weekday_chart(self, x0: int) -> str:
        """Returns weekday bars with percentage labels, highlighting the peak day."""
        total = sum(self.weekday_counts)
        if total == 0:
            return self._panel_header(x0, "By weekday", "No contributions yet")

        max_value = max(self.weekday_counts)
        peak_idx = self.weekday_counts.index(max_value)
        peak_pct = max_value / total * 100
        parts = [
            self._panel_header(
                x0, "By weekday", f"Peak: {self.WEEKDAY_FULL_NAMES[peak_idx]} ({peak_pct:.0f}%)"
            )
        ]

        bar_width = 36
        step = (self.PANEL_WIDTH - bar_width) / 6
        for slot, day in enumerate(self.WEEKDAY_ORDER):
            x = x0 + slot * step
            value = self.weekday_counts[day]
            parts.append(self._bar(x, bar_width, value, max_value, day == peak_idx))
            pct = value / total * 100
            label_y = self.BASELINE - max(value / max_value * self.MAX_BAR_HEIGHT, 3) - 6
            center = x + bar_width / 2
            parts.append(
                f'  <text x="{center:.2f}" y="{label_y:.2f}" text-anchor="middle" class="m3-body-small">{pct:.0f}%</text>\n'
                f'  <text x="{center:.2f}" y="{self.BASELINE + 18}" text-anchor="middle" class="m3-label-medium">{self.WEEKDAY_NAMES[day]}</text>\n'
            )
        return "".join(parts)

    def _get_hour_chart(self, x0: int) -> str:
        """Returns 24 hourly bars, highlighting the busiest four-hour window."""
        window = DataProcessor.peak_hour_window(self.hour_counts)
        if window is None:
            return self._panel_header(x0, "By hour (ET)", "No recent event data")

        start, end, label = window
        parts = [self._panel_header(x0, "By hour (ET)", f"Peak: {label}")]
        max_value = max(self.hour_counts)
        step = self.PANEL_WIDTH / 24
        for hour, value in enumerate(self.hour_counts):
            parts.append(
                self._bar(x0 + hour * step, step - 3, value, max_value, start <= hour < end)
            )
        for hour, text in [(0, "12 AM"), (6, "6 AM"), (12, "12 PM"), (18, "6 PM")]:
            parts.append(
                f'  <text x="{x0 + hour * step:.2f}" y="{self.BASELINE + 18}" class="m3-label-medium">{text}</text>\n'
            )
        return "".join(parts)


class TopReposDashboardGenerator(M3SVGGenerator):
    """Generates the Selected Repositories SVG dashboard in two columns."""

    COLUMN_WIDTH = 376
    ROW_HEIGHT = 100

    def __init__(
        self,
        top_repos: List[Tuple[str, str]],
        repos_data: List[Optional[Dict[str, Any]]],
        theme: str = "light",
        now: Optional[datetime] = None,
    ):
        """Initializes with the repositories data."""
        rows = (len(top_repos) + 1) // 2
        super().__init__(
            width=816,
            height=76 + rows * self.ROW_HEIGHT + 12,
            title="Selected Repositories Dashboard",
            desc="Shows selected repositories and their language composition",
            theme=theme,
        )
        self.top_repos = top_repos
        self.repos_data = repos_data
        self.now = now or datetime.now(timezone.utc)

    def generate(self) -> str:
        """Generates the Selected Repositories SVG."""
        content = [
            self._get_svg_header(),
            self._get_background_card(),
            self._get_title("Selected Repositories", "Featured projects breakdown"),
            self._get_repo_list(),
            self._get_svg_footer(),
        ]
        return "".join(content)

    def _get_repo_list(self) -> str:
        """Returns the grid of repository cards."""
        repo_items = []
        card_rect = (
            f'    <rect x="0" y="0" width="{self.COLUMN_WIDTH}" height="88" class="m3-card-medium" />\n'
        )

        for i, repo in enumerate(self.repos_data):
            x = 24 + (i % 2) * (self.COLUMN_WIDTH + 16)
            y = 76 + (i // 2) * self.ROW_HEIGHT

            if not repo:
                owner, name = self.top_repos[i]
                repo_items.append(
                    f'  <g transform="translate({x}, {y})">\n'
                    f"{card_rect}"
                    f'    <text x="16" y="24" class="m3-title-medium">{xml_escape(owner)}/{xml_escape(name)}</text>\n'
                    f'    <text x="16" y="44" class="m3-body-small" style="fill: var(--md-sys-color-error);">Repository not found or private.</text>\n'
                    f"  </g>"
                )
                continue

            owner = repo["owner"]["login"]
            name = repo["name"]
            full_name = f"{owner}/{name}"
            if len(full_name) > 26:
                full_name = full_name[:24] + "…"

            desc = repo.get("description") or "No description provided."
            if len(desc) > 52:
                desc = desc[:49] + "…"

            meta_parts = []
            if repo.get("stargazerCount") is not None:
                meta_parts.append(f"★ {repo['stargazerCount']:,}")
            age = relative_age(repo.get("pushedAt"), self.now)
            if age:
                meta_parts.append(f"updated {age}")
            meta = " · ".join(meta_parts)

            bar_width = self.COLUMN_WIDTH - 32
            langs = repo.get("languages", {}).get("edges", [])
            total_size = sum(edge["size"] for edge in langs)

            legend_rects = []
            if total_size > 0:
                legend_x = 16.0
                legend_end = 16 + bar_width
                shown = [
                    edge for edge in langs if edge["size"] / total_size * 100 >= 1
                ][:3]
                for edge in shown:
                    color = edge["node"]["color"] or FALLBACK_COLOR
                    pct = (edge["size"] / total_size) * 100
                    raw_lang_name = edge["node"]["name"]
                    raw_lang_name = LANGUAGE_ALIASES.get(raw_lang_name, raw_lang_name)
                    # Labels flow left to right. When a label would run past
                    # the bar, drop the decimal, then shorten the name, and
                    # stop when even a short stub cannot fit.
                    max_chars = int((legend_end - legend_x - 12) / LABEL_CHAR_WIDTH)
                    pct_text = f" {pct:.1f}%"
                    if len(raw_lang_name) + len(pct_text) > max_chars:
                        pct_text = f" {pct:.0f}%"
                    name_chars = max_chars - len(pct_text)
                    if len(raw_lang_name) > name_chars:
                        if name_chars < 4:
                            break
                        raw_lang_name = raw_lang_name[: name_chars - 1] + "…"
                    lang_name = xml_escape(raw_lang_name)
                    legend_rects.append(
                        f'      <circle cx="{legend_x + 4:.1f}" cy="72" r="4" fill="{color}"{self._swatch_stroke(color)} />\n'
                        f'      <text x="{legend_x + 12:.1f}" y="76" class="m3-label-medium">{lang_name}{pct_text}</text>'
                    )
                    label_width = (len(raw_lang_name) + len(pct_text)) * LABEL_CHAR_WIDTH
                    legend_x += max(112, 12 + label_width + 12)
            else:
                legend_rects.append(
                    '      <text x="16" y="76" class="m3-label-medium">No language data</text>'
                )

            bar = self._get_segmented_bar(
                f"repo-bar-clip-{i}",
                16,
                50,
                bar_width,
                6,
                [
                    (edge["size"], edge["node"]["color"] or FALLBACK_COLOR)
                    for edge in langs
                ],
            )
            legend_content = "\n".join(legend_rects)

            item = (
                f'  <g transform="translate({x}, {y})">\n'
                f"{card_rect}"
                f'    <text x="16" y="24" class="m3-title-medium">{xml_escape(full_name)}</text>\n'
                f'    <text x="{self.COLUMN_WIDTH - 16}" y="24" text-anchor="end" class="m3-body-small">{xml_escape(meta)}</text>\n'
                f'    <text x="16" y="42" class="m3-body-small">{xml_escape(desc)}</text>\n'
                f"{bar}"
                f"{legend_content}\n"
                f"  </g>"
            )
            repo_items.append(item)

        return "\n".join(repo_items)
