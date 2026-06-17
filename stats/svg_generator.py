"""Base class and concrete implementations for SVG generators."""

from typing import Dict, Any, List, Tuple, Optional
from stats.m3_design_system import M3Tokens


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


class M3SVGGenerator:
    """Base class for Material 3 SVG generation."""

    def __init__(self, width: int, height: int):
        """Initializes the generator with SVG dimensions."""
        self.width = width
        self.height = height

    def generate(self) -> str:
        """Generates the final SVG string. Must be implemented by subclasses."""
        raise NotImplementedError

    def _get_svg_header(self) -> str:
        """Returns the SVG root element and styles."""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}" fill="none">\\n'
            f"{M3Tokens.get_style_block()}\\n"
        )

    def _get_svg_footer(self) -> str:
        """Returns the closing SVG tag."""
        return "</svg>\\n"

    def _get_background_card(self) -> str:
        """Returns the main large container card."""
        return f'<rect class="m3-container-large" x="0.5" y="0.5" width="{self.width - 1}" height="{self.height - 1}" />\\n'


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
        cri: float,
        streak: int,
        peak_day: str,
        peak_hours: str,
        languages: Dict[str, Dict[str, Any]],
    ):
        """Initializes with all overview metrics."""
        super().__init__(width=600, height=300)
        self.total_stars = total_stars
        self.total_contributions = total_contributions
        self.total_repos = total_repos
        self.total_prs = total_prs
        self.total_reviews = total_reviews
        self.total_issues = total_issues
        self.cri = cri
        self.streak = streak
        self.peak_day = peak_day
        self.peak_hours = peak_hours
        self.languages = languages

    def generate(self) -> str:
        """Generates the Overview SVG."""
        content = [
            self._get_svg_header(),
            self._get_background_card(),
            self._get_header_section(),
            self._get_columns(),
            self._get_svg_footer(),
        ]
        return "".join(content)

    def _get_header_section(self) -> str:
        """Returns the header text."""
        return (
            '  <text x="24" y="36" class="m3-headline-small">GitHub Profile Overview</text>\\n'
            '  <text x="24" y="56" class="m3-body-small">Updated weekly • Public data only</text>\\n'
        )

    def _get_columns(self) -> str:
        """Returns the three columns with stats."""
        # Col 1: Activity
        col1 = '  <g transform="translate(24, 84)">\\n'
        col1 += '    <text x="0" y="0" class="m3-title-small">Engineering Activity</text>\\n'
        col1 += self._get_stat_row(0, 24, "Total Stars", str(self.total_stars))
        col1 += self._get_stat_row(
            0, 52, "Contributions", str(self.total_contributions)
        )
        col1 += self._get_stat_row(0, 80, "Merged PRs", str(self.total_prs))
        col1 += self._get_stat_row(0, 108, "Code Reviews", str(self.total_reviews))
        col1 += self._get_stat_row(0, 136, "Issues", str(self.total_issues))
        col1 += "  </g>\\n"

        # Divider 1
        divider1 = '  <line x1="190" y1="84" x2="190" y2="250" class="m3-divider" />\\n'

        # Col 2: Velocity & Impact
        col2 = '  <g transform="translate(210, 84)">\\n'
        col2 += '    <text x="0" y="0" class="m3-title-small">Velocity &amp; Impact</text>\\n'
        col2 += self._get_stat_row(0, 24, "Code Reuse", f"{self.cri:.1f}x")
        col2 += self._get_stat_row(0, 52, "Streak", f"{self.streak} Days")
        col2 += self._get_stat_row(0, 80, "Peak Day", xml_escape(self.peak_day))
        col2 += self._get_stat_row(0, 108, "Peak Hours", xml_escape(self.peak_hours))
        col2 += "  </g>\\n"

        # Divider 2
        divider2 = '  <line x1="390" y1="84" x2="390" y2="250" class="m3-divider" />\\n'

        # Col 3: Languages
        col3 = '  <g transform="translate(410, 84)">\\n'
        col3 += (
            '    <text x="0" y="0" class="m3-title-small">Languages (Core)</text>\\n'
        )
        col3 += self._get_language_breakdown()
        col3 += "  </g>\\n"

        return col1 + divider1 + col2 + divider2 + col3

    def _get_stat_row(self, x: int, y: int, label: str, value: str) -> str:
        """Returns a single stat row."""
        return (
            f'    <g transform="translate({x}, {y})">\\n'
            f'      <text x="0" y="12" class="m3-body-medium">{label}</text>\\n'
            f'      <text x="100" y="12" class="m3-label-large">{value}</text>\\n'
            f"    </g>\\n"
        )

    def _get_language_breakdown(self) -> str:
        """Returns the language bar and legend."""
        total_size = sum(lang["size"] for lang in self.languages.values())
        bar_rects = []
        legend_items = []

        total_bar_width = 160.0

        if total_size > 0:
            sorted_langs = sorted(
                self.languages.items(), key=lambda x: x[1]["size"], reverse=True
            )
            top_6 = sorted_langs[:6]
            other_size = sum(lang[1]["size"] for lang in sorted_langs[6:])

            legend_data = []
            for name, data in top_6:
                pct = (data["size"] / total_size) * 100
                legend_data.append(
                    {"name": name, "pct": pct, "color": data["color"] or "#8e918f"}
                )

            if other_size > 0:
                pct_other = (other_size / total_size) * 100
                legend_data.append(
                    {"name": "Other", "pct": pct_other, "color": "#8e918f"}
                )

            current_x = 0.0
            for item in legend_data:
                w = (item["pct"] / 100.0) * total_bar_width
                if w > 0:
                    bar_rects.append(
                        f'<rect x="{current_x:.2f}" y="0" width="{w:.2f}" height="8" '
                        f'fill="{item["color"]}" />'
                    )
                    current_x += w

            for idx, item in enumerate(legend_data):
                item_x = 0
                item_y = 36 + idx * 24

                lang_name = item["name"]
                if len(lang_name) > 12:
                    display_name = lang_name[:9] + "..."
                else:
                    display_name = lang_name

                escaped_name = xml_escape(display_name)
                pct_text = f"{item['pct']:.1f}%"

                legend_items.append(
                    f'      <g transform="translate({item_x}, {item_y})">\\n'
                    f'        <circle cx="5" cy="8" r="4.5" fill="{item["color"]}" />\\n'
                    f'        <text x="16" y="12" class="m3-body-medium">{escaped_name}</text>\\n'
                    f'        <text x="120" y="12" class="m3-body-small">{pct_text}</text>\\n'
                    f"      </g>"
                )
        else:
            bar_rects.append(
                f'<rect x="0" y="0" width="{total_bar_width}" height="8" class="m3-card-medium" />'
            )
            legend_items.append(
                '      <g transform="translate(0, 36)">\\n'
                '        <circle cx="5" cy="8" r="4.5" fill="var(--md-sys-color-outline-variant)" />\\n'
                '        <text x="16" y="12" class="m3-body-medium">No data</text>\\n'
                "      </g>"
            )

        bar_content = "\\n      ".join(bar_rects)
        legend_content = "\\n".join(legend_items)

        # Clip path for rounded bar ends
        return (
            '    <clipPath id="bar-clip">\\n'
            f'      <rect width="{total_bar_width}" height="8" rx="4" />\\n'
            "    </clipPath>\\n"
            '    <g transform="translate(0, 16)" clip-path="url(#bar-clip)">\\n'
            f'      <rect width="{total_bar_width}" height="8" fill="var(--md-sys-color-surface-variant)" />\\n'
            f"      {bar_content}\\n"
            "    </g>\\n"
            f"{legend_content}\\n"
        )


class TopReposDashboardGenerator(M3SVGGenerator):
    """Generates the Top Repositories SVG dashboard."""

    def __init__(
        self,
        top_repos: List[Tuple[str, str]],
        repos_data: List[Optional[Dict[str, Any]]],
    ):
        """Initializes with the repositories data."""
        # Base height for header is ~80px. Each repo takes ~72px.
        height = 80 + len(top_repos) * 72
        super().__init__(width=600, height=height)
        self.top_repos = top_repos
        self.repos_data = repos_data

    def generate(self) -> str:
        """Generates the Top Repositories SVG."""
        content = [
            self._get_svg_header(),
            self._get_background_card(),
            self._get_header_section(),
            self._get_repo_list(),
            self._get_svg_footer(),
        ]
        return "".join(content)

    def _get_header_section(self) -> str:
        """Returns the header text."""
        return (
            '  <text x="24" y="36" class="m3-headline-small">Top Repositories</text>\\n'
            '  <text x="24" y="56" class="m3-body-small">Featured projects breakdown • Updated weekly</text>\\n'
        )

    def _get_repo_list(self) -> str:
        """Returns the list of repositories."""
        repo_items = []

        for i, repo in enumerate(self.repos_data):
            y = 76 + i * 72

            if not repo:
                owner, name = self.top_repos[i]
                repo_items.append(
                    f'  <g transform="translate(24, {y})">\\n'
                    f'    <text x="0" y="16" class="m3-title-medium">{xml_escape(owner)}/{xml_escape(name)}</text>\\n'
                    f'    <text x="0" y="36" class="m3-body-small" style="fill: var(--md-sys-color-error);">Repository not found or private.</text>\\n'
                    f"  </g>"
                )
                continue

            owner = repo["owner"]["login"]
            name = repo["name"]
            full_name = f"{owner}/{name}"

            # Truncate description more aggressively if needed
            desc = repo.get("description") or "No description provided."
            if len(desc) > 80:
                desc = desc[:77] + "..."

            stars = repo.get("stargazerCount", 0)
            forks = repo.get("forkCount", 0)
            releases = repo.get("releases", {}).get("totalCount", 0)
            lang = repo.get("primaryLanguage")

            lang_name = lang["name"] if lang else "None"
            lang_color = (
                lang["color"] if lang else "var(--md-sys-color-outline-variant)"
            )

            # Draw individual card
            card_rect = f'    <rect x="0" y="0" width="552" height="64" class="m3-card-medium" />\\n'

            item = (
                f'  <g transform="translate(24, {y})">\\n'
                f"{card_rect}"
                f'    <text x="16" y="24" class="m3-title-medium">{xml_escape(full_name)}</text>\\n'
                f'    <text x="16" y="44" class="m3-body-small">{xml_escape(desc)}</text>\\n'
                # Language
                f'    <circle cx="330" cy="20" r="4.5" fill="{lang_color}" />\\n'
                f'    <text x="340" y="24" class="m3-label-medium">{xml_escape(lang_name)}</text>\\n'
                # Stars
                f'    <text x="420" y="24" class="m3-label-medium">⭐ {stars}</text>\\n'
                # Forks
                f'    <text x="470" y="24" class="m3-label-medium">🍴 {forks}</text>\\n'
                # Releases
                f'    <text x="520" y="24" class="m3-label-medium">📦 {releases}</text>\\n'
                f"  </g>"
            )
            repo_items.append(item)

        return "\\n".join(repo_items)
