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

    def __init__(
        self,
        width: int,
        height: int,
        title: str = "GitHub Stats",
        desc: str = "GitHub statistics dashboard",
    ):
        """Initializes the generator with SVG dimensions."""
        self.width = width
        self.height = height
        self.title = title
        self.desc = desc

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
            f"{M3Tokens.get_style_block()}\n"
        )

    def _get_svg_footer(self) -> str:
        """Returns the closing SVG tag."""
        return "</svg>\n"

    def _get_background_card(self) -> str:
        """Returns the main large container card."""
        return f'<rect class="m3-container-large" x="0.5" y="0.5" width="{self.width - 1}" height="{self.height - 1}" />\n'


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
        peak_day: str,
        peak_hours: str,
    ):
        """Initializes with all overview metrics."""
        super().__init__(width=600, height=240)
        self.total_stars = total_stars
        self.total_contributions = total_contributions
        self.total_repos = total_repos
        self.total_prs = total_prs
        self.total_reviews = total_reviews
        self.total_issues = total_issues
        self.streak = streak
        self.peak_day = peak_day
        self.peak_hours = peak_hours

    def generate(self) -> str:
        """Generates the Overview SVG."""
        content = [
            self._get_svg_header(),
            self._get_background_card(),
            self._get_header_section(),
            self._get_grid(),
            self._get_svg_footer(),
        ]
        return "".join(content)

    def _get_header_section(self) -> str:
        """Returns the header text."""
        return (
            '  <text x="24" y="36" class="m3-headline-small">GitHub Profile Overview</text>\n'
            '  <text x="24" y="56" class="m3-body-small">Public data only</text>\n'
        )

    def _get_grid(self) -> str:
        """Returns the 3x3 grid with stats."""
        grid_html = ""

        # Row 1
        grid_html += self._get_stat_item(
            24, 84, "stars", "Total Stars", str(self.total_stars)
        )
        grid_html += self._get_stat_item(
            224, 84, "contributions", "Contributions", str(self.total_contributions)
        )
        grid_html += self._get_stat_item(
            424, 84, "prs", "Merged PRs", str(self.total_prs)
        )

        # Row 2
        grid_html += self._get_stat_item(
            24, 134, "reviews", "Code Reviews", str(self.total_reviews)
        )
        grid_html += self._get_stat_item(
            224, 134, "issues", "Issues", str(self.total_issues)
        )
        grid_html += self._get_stat_item(
            424, 134, "streak", "Streak", f"{self.streak} Days"
        )

        # Row 3
        grid_html += self._get_stat_item(
            24, 184, "peak_day", "Peak Day", xml_escape(self.peak_day)
        )
        grid_html += self._get_stat_item(
            224, 184, "peak_hours", "Peak Hours", xml_escape(self.peak_hours)
        )

        return grid_html

    def _get_stat_item(
        self, x: int, y: int, icon_name: str, label: str, value: str
    ) -> str:
        """Returns a single stat item with an icon."""
        icon_path = M3Tokens.ICONS.get(icon_name, "")
        return (
            f'  <g transform="translate({x}, {y})">\n'
            f'    <svg x="0" y="-4" width="20" height="20" viewBox="0 0 24 24" fill="var(--md-sys-color-primary)">\n'
            f'      <path d="{icon_path}"/>\n'
            f"    </svg>\n"
            f'    <text x="28" y="12" class="m3-body-medium">{label}</text>\n'
            f'    <text x="28" y="32" class="m3-label-large">{value}</text>\n'
            f"  </g>\n"
        )


class LanguagesDashboardGenerator(M3SVGGenerator):
    """Generates the Languages SVG dashboard."""

    def __init__(
        self,
        languages: Dict[str, Dict[str, Any]],
    ):
        """Initializes with languages data."""
        super().__init__(
            width=600,
            height=260,
            title="Top Languages Dashboard",
            desc="Shows a bar chart of top programming languages used",
        )
        self.languages = languages

    def generate(self) -> str:
        """Generates the Languages SVG."""
        content = [
            self._get_svg_header(),
            self._get_background_card(),
            self._get_header_section(),
            self._get_language_breakdown(),
            self._get_svg_footer(),
        ]
        return "".join(content)

    def _get_header_section(self) -> str:
        """Returns the header text."""
        return (
            '  <text x="24" y="36" class="m3-headline-small">Top Languages</text>\n'
            '  <text x="24" y="56" class="m3-body-small">Based on repository size</text>\n'
        )

    def _get_language_breakdown(self) -> str:
        """Returns the language bar and legend in two columns."""
        total_size = sum(lang["size"] for lang in self.languages.values())
        bar_rects = []
        legend_items = []

        total_bar_width = 552.0  # Width of the bar across the card (600 - 48)

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
                        f'<rect x="{current_x:.2f}" y="0" width="{w:.2f}" height="12" '
                        f'fill="{item["color"]}" />'
                    )
                    current_x += w

            for idx, item in enumerate(legend_data):
                col = idx % 2
                row = idx // 2
                item_x = 24 + (col * 276)
                item_y = 120 + (row * 30)

                lang_name = item["name"]
                if len(lang_name) > 20:
                    display_name = lang_name[:17] + "..."
                else:
                    display_name = lang_name

                escaped_name = xml_escape(display_name)
                pct_text = f"{item['pct']:.1f}%"

                legend_items.append(
                    f'  <g transform="translate({item_x}, {item_y})">\n'
                    f'    <circle cx="6" cy="6" r="6" fill="{item["color"]}" />\n'
                    f'    <text x="24" y="11" class="m3-body-large">{escaped_name}</text>\n'
                    f'    <text x="200" y="11" class="m3-label-large">{pct_text}</text>\n'
                    f"  </g>\n"
                )
        else:
            bar_rects.append(
                f'<rect x="0" y="0" width="{total_bar_width}" height="12" class="m3-card-medium" />'
            )
            legend_items.append(
                '  <g transform="translate(24, 120)">\n'
                '    <circle cx="6" cy="6" r="6" fill="var(--md-sys-color-outline-variant)" />\n'
                '    <text x="24" y="11" class="m3-body-large">No data</text>\n'
                "  </g>"
            )

        bar_content = "\n      ".join(bar_rects)
        legend_content = "\n".join(legend_items)

        # Clip path for rounded bar ends
        return (
            '  <clipPath id="lang-bar-clip">\n'
            f'    <rect width="{total_bar_width}" height="12" rx="6" />\n'
            "  </clipPath>\n"
            '  <g transform="translate(24, 84)" clip-path="url(#lang-bar-clip)">\n'
            f'    <rect width="{total_bar_width}" height="12" fill="var(--md-sys-color-surface-variant)" />\n'
            f"    {bar_content}\n"
            "  </g>\n"
            f"{legend_content}\n"
        )


class TopReposDashboardGenerator(M3SVGGenerator):
    """Generates the Top Repositories SVG dashboard."""

    def __init__(
        self,
        top_repos: List[Tuple[str, str]],
        repos_data: List[Optional[Dict[str, Any]]],
    ):
        """Initializes with the repositories data."""
        # Base height for header is ~80px. Each repo takes ~96px.
        height = 80 + len(top_repos) * 96
        super().__init__(
            width=600,
            height=height,
            title="Top Repositories Dashboard",
            desc="Shows top repositories and their language composition",
        )
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
            '  <text x="24" y="36" class="m3-headline-small">Top Repositories</text>\n'
            '  <text x="24" y="56" class="m3-body-small">Featured projects breakdown</text>\n'
        )

    def _get_repo_list(self) -> str:
        """Returns the list of repositories."""
        repo_items = []

        for i, repo in enumerate(self.repos_data):
            y = 76 + i * 96

            if not repo:
                owner, name = self.top_repos[i]
                repo_items.append(
                    f'  <g transform="translate(24, {y})">\n'
                    f'    <text x="0" y="16" class="m3-title-medium">{xml_escape(owner)}/{xml_escape(name)}</text>\n'
                    f'    <text x="0" y="36" class="m3-body-small" style="fill: var(--md-sys-color-error);">Repository not found or private.</text>\n'
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

            langs = repo.get("languages", {}).get("edges", [])
            total_size = sum(edge["size"] for edge in langs)

            bar_rects = []
            legend_rects = []
            if total_size > 0:
                current_x = 16.0
                legend_x = 16.0
                for j, edge in enumerate(langs):
                    size = edge["size"]
                    color = edge["node"]["color"] or "#8e918f"
                    w = (size / total_size) * 520.0
                    if w > 0:
                        bar_rects.append(
                            f'<rect x="{current_x:.2f}" y="48" width="{w:.2f}" height="6" fill="{color}" />'
                        )
                        current_x += w

                    if j < 4:  # Show max 4 items in legend
                        pct = (size / total_size) * 100
                        lang_name = xml_escape(edge["node"]["name"])
                        legend_rects.append(
                            f'      <circle cx="{legend_x + 4}" cy="72" r="4" fill="{color}" />\n'
                            f'      <text x="{legend_x + 12}" y="76" class="m3-label-medium">{lang_name} {pct:.1f}%</text>'
                        )
                        legend_x += 16 + len(lang_name) * 7 + 40
            else:
                bar_rects.append(
                    f'<rect x="16" y="48" width="520" height="6" fill="var(--md-sys-color-outline-variant)" />'
                )
                legend_rects.append(
                    f'      <text x="16" y="76" class="m3-label-medium">No language data</text>'
                )

            bar_content = "\n      ".join(bar_rects)
            legend_content = "\n".join(legend_rects)

            # Draw individual card
            card_rect = f'    <rect x="0" y="0" width="552" height="88" class="m3-card-medium" />\n'

            item = (
                f'  <g transform="translate(24, {y})">\n'
                f"{card_rect}"
                f'    <text x="16" y="24" class="m3-title-medium">{xml_escape(full_name)}</text>\n'
                f'    <text x="16" y="40" class="m3-body-small">{xml_escape(desc)}</text>\n'
                f'    <clipPath id="repo-bar-clip-{i}">\n'
                f'      <rect x="16" y="48" width="520" height="6" rx="3" />\n'
                f"    </clipPath>\n"
                f'    <g clip-path="url(#repo-bar-clip-{i})">\n'
                f'      <rect x="16" y="48" width="520" height="6" fill="var(--md-sys-color-surface-variant)" />\n'
                f"      {bar_content}\n"
                f"    </g>\n"
                f"      {legend_content}\n"
                f"  </g>"
            )
            repo_items.append(item)

        return "\n".join(repo_items)
